import polars as pl
import numpy as np
import faicons as fa
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_widget
import plotly.express as px
from plotly import graph_objects as go
from data import (
    get_unique_docket_ids,
    fetch_comments_df,
)
from botmirror import get_duplicate_groups, calculate_similarities


ICONS = {
    "comments": fa.icon_svg("comments"),
    "copy": fa.icon_svg("copy", style="regular"),
    "fingerprint": fa.icon_svg("fingerprint", style="solid"),
}

DEFAULT_AGENCIES = ["DEA"]

df = None
all_docket_labels, agency_codes, years = get_unique_docket_ids()


def _placeholder_fig(annotation_text: str = ""):
    """Create a an empty placeholder figure"""
    fig = go.Figure()

    fig.add_annotation(
        x=0.5,
        y=0.5,
        text=annotation_text,
        showarrow=False,
        font=dict(size=16),
        xref="paper",
        yref="paper",
    )
    fig.update_layout(
        template="plotly_white",
        xaxis=dict(range=[0, 1]),
        yaxis=dict(range=[0, 1]),
    )

    return fig


main_pannel = ui.page_sidebar(
    ui.sidebar(
        ui.input_checkbox_group(
            id="agency_picker",
            label="Select Agency Code",
            choices=agency_codes,
            selected=agency_codes,
        ),
        ui.input_selectize(
            id="year_picker", label="Select Year", choices=years, multiple=True
        ),
        ui.input_select(
            id="docket_picker",
            label="Select Docket ID",
            choices=all_docket_labels,
        ),
    ),
    ui.card(
        ui.card_header("Overview"),
        ui.layout_columns(
            ui.value_box(
                title="Total Comments",
                value=ui.output_ui("total_comments"),
                showcase=ICONS["comments"],
                theme="bg-teal",
            ),
            ui.value_box(
                title="Nr. Unique Comments",
                value=ui.output_ui("unique_comments"),
                showcase=ICONS["fingerprint"],
                theme="bg-teal",
            ),
            ui.value_box(
                title="Nr. Comments With Duplicates",
                value=ui.output_ui("total_duplicates"),
                showcase=ICONS["copy"],
                theme="bg-teal",
            ),
            fill=False,
        ),
        # ui.output_data_frame(id="preview"),
        output_widget(id="duplicates_plot"),
    ),
    ui.br(),
    ui.output_text(id="selected_docket"),
    ui.input_action_button(
        id="compute_similarity",
        label="Find similar comments",
    ),
    ui.br(),
    ui.br(),
    ui.card(
        ui.card_header("Similarity analysis"),
        ui.input_slider(
            id="similarity_range",
            label="Similarity Score Range",
            min=0,
            max=100,
            value=[50, 100],
            step=1,
        ),
        output_widget(id="similarity_plot"),
        ui.layout_columns(
            ui.card(ui.card_header("Reference text"), ui.output_ui(id="ref_text")),
            ui.card(
                ui.card_header("Compared comment"),
                ui.output_ui(id="compared_comment"),
            ),
        ),
    ),
)


def server(input, output, session):
    @reactive.calc
    def load_data():
        global df

        df = fetch_comments_df(docket_id=input.docket_picker())

        return df

    @reactive.effect
    def compute_similarities():
        current_count = input.compute_similarity()
        old_count = last_button_count.get()
        clicked_data = clicked_bar.get()

        # Only run when button count has incremented and we have clicked data
        if current_count > old_count and clicked_data:
            with ui.Progress() as p:
                comments_df = load_data()

                # Get the point index to access customdata
                point_index = clicked_data["points"].point_inds[0]
                trace = clicked_data["trace"]

                # Access customdata from the trace
                ref_text = trace.customdata[point_index][0]
                content_hash = trace.customdata[point_index][1]

                n_comments_to_compare = len(
                    comments_df.filter(
                        pl.col("content_hash") != content_hash, pl.col("is_duplicate")
                    )
                )

                p.set(
                    message=f"Computing similarities over {n_comments_to_compare:,} comments. Hang on..."
                )

                similarity_df = calculate_similarities(
                    df=comments_df, reference_text=ref_text, exclude_hash=content_hash
                )

                print(f"Similarity results shape: {similarity_df.shape}")
                print(f"Top 5 similar comments:\n{similarity_df.head()}")

                # Store the results
                similarity_results.set(similarity_df)

                print(f"old_count: {old_count}")
                print(f"current_count: {current_count}")

                # Update the stored count
                last_button_count.set(current_count)

    @reactive.effect
    def _():
        years_new = [int(v) for v in input.year_picker()]

        docket_ids_new, _, _ = get_unique_docket_ids(
            agency_codes=input.agency_picker(), years=years_new
        )

        ui.update_select(
            id="docket_picker",
            label="Select Docket ID",
            choices=docket_ids_new,
        )

    @render.ui
    def total_comments():
        return f"{len(load_data()):,}"

    @render.ui
    def unique_comments():
        return f"{len(load_data()['content_hash'].unique()):,}"

    @render.ui
    def total_duplicates():
        df = load_data()

        if df.is_empty():
            return "None found"
        else:
            duplicates_df = get_duplicate_groups(load_data())
        return f"{len(duplicates_df):,}"

    clicked_bar = reactive.value(None)
    clicked_line = reactive.value(None)
    similarity_results = reactive.value(None)
    last_button_count = reactive.value(0)
    reference_text = reactive.value("")
    compared_text = reactive.value("")

    def clear_markers(fig_widget, marker_color, marker_type):
        # Remove existing red bar traces
        traces_to_remove = []
        for i, existing_trace in enumerate(fig_widget.data):
            if (
                hasattr(existing_trace, "marker")
                and hasattr(existing_trace.marker, "color")
                and existing_trace.marker.color == marker_color
                and existing_trace.type == marker_type
            ):
                traces_to_remove.append(i)

        # Remove old red bars in reverse order
        for i in reversed(traces_to_remove):
            fig_widget.data = fig_widget.data[:i] + fig_widget.data[i + 1 :]

        return fig_widget

    def on_bar_click(trace, points, state):
        # Store both points and trace for accessing customdata
        clicked_data = {"points": points, "trace": trace}
        clicked_bar.set(clicked_data)

        # Extract and store reference text from customdata
        point_index = points.point_inds[0]
        ref_text = trace.customdata[point_index][0]
        reference_text.set(ref_text)

        # Get the parent figure widget from the trace
        fig_widget = trace.parent

        # Only modify if this is the duplicates plot (check trace name or other identifier)
        if len(fig_widget.data) > 0 and hasattr(fig_widget.data[0], "customdata"):
            fig_widget = clear_markers(
                fig_widget=fig_widget, marker_color="red", marker_type="bar"
            )

            # Add new red bar at clicked point with same height
            fig_widget.add_bar(
                x=[points.xs[0]],
                y=[points.ys[0]],
                marker=dict(color="red", opacity=0.8),
                hoverinfo="skip",  # Disable hover for this marker
                showlegend=False,
                base=0,  # Start from baseline
            )

    @render_widget
    def duplicates_plot():
        df = load_data()

        if df.is_empty():
            return _placeholder_fig("No data found")
        else:
            duplicates_df = get_duplicate_groups(load_data())

        if len(duplicates_df) == 0:
            return _placeholder_fig("No duplicate comments found")
        else:
            duplicates_df = get_duplicate_groups(load_data())
            x_vals = np.arange(0, len(duplicates_df)) + 1

            # Extract first comment from each row for customdata
            first_comments = duplicates_df["comment"].list.get(0).to_list()
            content_hashes = duplicates_df["content_hash"].to_list()

            print(f"duplicates_df: {duplicates_df.head()}")

            fig = px.bar(
                data_frame=duplicates_df,
                x=x_vals,
                y="len",
                log_y=True,
                color_discrete_sequence=px.colors.qualitative.D3,
                custom_data=[first_comments, content_hashes],
            )

            fig.update_traces(
                hovertemplate="<b>Comment ID:</b> %{x}<br><b>Count:</b>%{y}<extra></extra>",
            )

            fig.update_layout(
                title="Comments with duplicates (sorted)",
                yaxis_title="Count",
                xaxis_title="Comment ID",
                template="plotly_white",
            )

            fig_widget = go.FigureWidget(fig.data, fig.layout)
            fig_widget.data[0].on_click(on_bar_click)

            return fig_widget

    def on_line_click(trace, points, state):
        # Store both points and trace for accessing customdata
        clicked_data = {"points": points, "trace": trace}
        clicked_line.set(clicked_data)

        # Extract and store compared text from customdata
        point_index = points.point_inds[0]
        comp_text = trace.customdata[point_index][0]
        compared_text.set(comp_text)

        # Get the parent figure widget from the trace
        fig_widget = trace.parent

        # Only modify if this is the duplicates plot (check trace name or other identifier)
        if len(fig_widget.data):
            fig_widget = clear_markers(
                fig_widget=fig_widget, marker_color="red", marker_type="scatter"
            )

            # Add new red marker at clicked point
            fig_widget.add_scatter(
                x=[points.xs[0]],
                y=[points.ys[0]],
                mode="markers",
                marker=dict(size=8, color="red"),
                hoverinfo="skip",  # Disable hover for this marker
                showlegend=False,
            )

    @render_widget
    def similarity_plot():
        similarity_df = similarity_results.get()

        if similarity_df is None or similarity_df.is_empty():
            return _placeholder_fig(
                "No similarity data found. Click a bar and compute similarities."
            )

        # Filter based on similarity range
        min_sim, max_sim = input.similarity_range()
        filtered_df = similarity_df.filter(
            (pl.col("similarity") >= min_sim) & (pl.col("similarity") <= max_sim)
        )

        if filtered_df.is_empty():
            return _placeholder_fig(
                f"No comments in similarity range {min_sim}-{max_sim}"
            )

        # Create x values for the line plot
        x_vals = np.arange(0, len(filtered_df)) + 1

        # Extract text content for customdata
        compared_texts = filtered_df["comment"].to_list()

        fig = px.line(
            data_frame=filtered_df,
            x=x_vals,
            y="similarity",
            color_discrete_sequence=px.colors.qualitative.D3,
            markers=True,
            custom_data=[compared_texts],
        )

        fig.update_traces(
            hovertemplate="<b>Comment ID:</b> %{x}<br><b>Similarity Score:</b>%{y}<extra></extra>"
        )

        fig.update_layout(
            title="Similar Comments (sorted by similarity)",
            yaxis_title="Similarity Score",
            xaxis_title="Comment Rank",
            template="plotly_white",
        )

        fig_widget = go.FigureWidget(fig.data, fig.layout)
        fig_widget.data[0].on_click(on_line_click)

        return fig_widget

    @render.text
    def selected_docket():
        clicked_data = clicked_bar.get()
        if clicked_data:
            comment_id = clicked_data["points"].xs[0]
            n_duplicates = clicked_data["points"].ys[0]
        else:
            return "No comment selected"

        return f"Selected Comment ID: {comment_id} (nr. duplicates: {n_duplicates})"

    @render.ui
    def ref_text():
        ref_text = reference_text.get()
        if ref_text:
            return ui.div(
                ui.p(
                    ref_text,
                    style="white-space: pre-wrap; font-family: monospace; padding: 10px; background-color: #f8f9fa; border-radius: 5px; margin: 0;",
                )
            )
        return ui.p(
            "Click a bar in the duplicates plot to select reference text",
            style="font-style: italic; color: #666;",
        )

    @render.ui
    def compared_comment():
        comp_text_value = compared_text.get()
        if comp_text_value:
            return ui.div(
                ui.p(
                    comp_text_value,
                    style="white-space: pre-wrap; font-family: monospace; padding: 10px; background-color: #f8f9fa; border-radius: 5px; margin: 0;",
                )
            )
        return ui.p(
            "Click a point in the similarity plot to select compared text",
            style="font-style: italic; color: #666;",
        )

    # @render.data_frame
    # def preview():
    #
    #    df = load_data()
    #    print(df.head())
    #    return render.DataGrid(df.head())


app = App(main_pannel, server)
