import dash
from dash import html, dcc, Input, Output, State, ctx, ALL
import plotly.graph_objects as go
import webbrowser
from threading import Timer

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Beleid Overzicht Meter (B.O.M.)"

app.layout = html.Div(
    [
        # Header with two logos (stacked) and Dutch title
        html.Div(
            [
                html.Div(
                    [
                        html.Img(
                            src="/assets/enschede.png",
                            style={"height": "40px", "width": "auto", "objectFit": "contain", "marginBottom": "6px"},
                        ),
                        html.Img(
                            src="/assets/unilogo.png",
                            style={"height": "50px", "width": "auto", "objectFit": "contain"},
                        ),
                    ],
                    style={"display": "flex", "flexDirection": "column", "alignItems": "flex-start", "marginRight": "15px"},
                ),
                html.H1(
                    "Beleid Overzicht Meter (B.O.M.)",
                    style={"margin": "0", "marginLeft": "auto", "textAlign": "right"},
                ),
            ],
            style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "15px"},
        ),

        # Stores
        dcc.Store(id="goals-store", data=[]),
        dcc.Store(id="projects-store", data=[]),
        dcc.Store(id="edit-project-store", data=None),  # index being edited or None

        # Action buttons
        html.Div(
            [
                html.Button("+ Doel toevoegen", id="add-goal-btn", n_clicks=0,
                            style={"fontSize": "18px", "marginRight": "10px", "background": "#007BFF", "color": "white"}),
                html.Button("+ Project toevoegen", id="add-project-btn", n_clicks=0,
                            style={"fontSize": "18px", "background": "#28A745", "color": "white"}),
            ],
            style={"marginBottom": "10px"},
        ),

        html.Div(id="forms-container", style={"marginBottom": "10px"}),
        html.Hr(style={"marginTop": "10px", "marginBottom": "10px"}),
        html.Div(id="dashboard-content"),
    ],
    style={"fontFamily": "Arial", "padding": "20px", "maxWidth": "1000px", "margin": "auto"},
)


# ---- Add Goal form (show) ----
@app.callback(
    Output("forms-container", "children", allow_duplicate=True),
    Input("add-goal-btn", "n_clicks"),
    prevent_initial_call=True,
)
def show_goal_form(n):
    if not n:
        return dash.no_update
    return html.Div(
        [
            html.H3("Nieuw doel toevoegen"),
            dcc.Input(id={"type": "goal-form", "name": "goal-name"}, placeholder="Naam van het doel", type="text", style={"marginRight": "10px", "width": "220px"}),
            dcc.Input(id={"type": "goal-form", "name": "goal-target"}, placeholder="Streefwaarde", type="number", style={"marginRight": "10px", "width": "140px"}),
            dcc.Input(id={"type": "goal-form", "name": "goal-unit"}, placeholder="Eenheid (bijv. %, bomen, km, euro)", type="text", style={"marginRight": "10px", "width": "200px"}),
            html.Button("Opslaan", id={"type": "goal-form", "name": "save-goal"}, style={"background": "#007BFF", "color": "white"}),
            html.Button("Annuleren", id={"type": "goal-form", "name": "cancel-goal"}, style={"marginLeft": "10px"}),
        ]
    )


# ---- Save / Cancel goal ----
@app.callback(
    Output("goals-store", "data", allow_duplicate=True),
    Output("forms-container", "children", allow_duplicate=True),
    Input({"type": "goal-form", "name": "save-goal"}, "n_clicks"),
    Input({"type": "goal-form", "name": "cancel-goal"}, "n_clicks"),
    State({"type": "goal-form", "name": "goal-name"}, "value"),
    State({"type": "goal-form", "name": "goal-target"}, "value"),
    State({"type": "goal-form", "name": "goal-unit"}, "value"),
    State("goals-store", "data"),
    prevent_initial_call=True,
)
def handle_goal_actions(save_clicks, cancel_clicks, name, target, unit, goals):
    goals = goals or []
    trigger = ctx.triggered_id
    if not trigger:
        return dash.no_update, dash.no_update

    if trigger["name"] == "save-goal" and name and target is not None:
        goals.append({"name": name, "target": float(target), "unit": unit or ""})
        return goals, html.Div()
    if trigger["name"] == "cancel-goal":
        return goals, html.Div()
    return dash.no_update, dash.no_update


# ---- Delete a goal (narrower delete button) ----
@app.callback(
    Output("goals-store", "data"),
    Input({"type": "delete-goal-btn", "index": ALL}, "n_clicks"),
    State("goals-store", "data"),
    prevent_initial_call=True,
)
def delete_goal(delete_clicks, goals):
    goals = goals or []
    for i, n in enumerate(delete_clicks):
        if n:
            goals.pop(i)
            break
    return goals


# ---- Show Add Project form ----
@app.callback(
    Output("forms-container", "children", allow_duplicate=True),
    Input("add-project-btn", "n_clicks"),
    State("goals-store", "data"),
    prevent_initial_call=True,
)
def show_project_form(n, goals):
    if not n:
        return dash.no_update
    if not goals:
        return html.Div("⚠️ Voeg eerst minstens één doel toe.", style={"color": "darkred"})

    inputs = []
    for g in goals:
        unit = g.get("unit", "%") or "%"
        inputs.append(
            html.Div(
                [
                    html.Label(f"Bijdrage aan {g['name']} ({unit})"),
                    dcc.Input(id={"type": "project-form", "goal": g["name"]}, type="number", placeholder=f"bijv. 10 ({unit})", style={"marginLeft": "10px", "width": "120px"}),
                ],
                style={"marginBottom": "8px"},
            )
        )

    return html.Div(
        [
            html.H3("Nieuw project toevoegen"),
            dcc.Input(id={"type": "project-form", "name": "project-name"}, placeholder="Naam van het project", type="text", style={"marginRight": "10px", "marginBottom": "10px", "width": "300px"}),
            dcc.Textarea(id={"type": "project-form", "name": "project-description"}, placeholder="Beschrijving van het project (optioneel)", style={"width": "100%", "height": "80px", "marginBottom": "10px"}),
            html.Div(inputs),
            html.Button("Opslaan", id={"type": "project-form", "name": "save-project"}, style={"background": "#28A745", "color": "white", "marginTop": "10px"}),
            html.Button("Annuleren", id={"type": "project-form", "name": "cancel-project"}, style={"marginLeft": "10px", "marginTop": "10px"}),
        ]
    )


# ---- Save / Cancel project ----
@app.callback(
    Output("projects-store", "data", allow_duplicate=True),
    Output("forms-container", "children", allow_duplicate=True),
    Input({"type": "project-form", "name": "save-project"}, "n_clicks"),
    Input({"type": "project-form", "name": "cancel-project"}, "n_clicks"),
    State({"type": "project-form", "name": "project-name"}, "value"),
    State({"type": "project-form", "name": "project-description"}, "value"),
    State({"type": "project-form", "goal": ALL}, "value"),
    State("goals-store", "data"),
    State("projects-store", "data"),
    prevent_initial_call=True,
)
def handle_project_actions(save_clicks, cancel_clicks, name, description, contributions, goals, projects):
    projects = projects or []
    trigger = ctx.triggered_id
    if not trigger:
        return dash.no_update, dash.no_update
    if trigger["name"] == "save-project" and name:
        contrib_data = {g["name"]: float(c or 0) for g, c in zip(goals, contributions)}
        projects.append({"name": name, "description": description or "", "contributions": contrib_data})
        return projects, html.Div()
    if trigger["name"] == "cancel-project":
        return projects, html.Div()
    return dash.no_update, dash.no_update


# ---- Delete a project ----
@app.callback(
    Output("projects-store", "data"),
    Input({"type": "delete-project-btn", "index": ALL}, "n_clicks"),
    State("projects-store", "data"),
    prevent_initial_call=True,
)
def delete_project(delete_clicks, projects):
    projects = projects or []
    for i, n in enumerate(delete_clicks):
        if n:
            projects.pop(i)
            break
    return projects


# ---- Start editing: set edit-project-store to index ----
@app.callback(
    Output("edit-project-store", "data"),
    Input({"type": "edit-project-btn", "index": ALL}, "n_clicks"),
    State("edit-project-store", "data"),
    prevent_initial_call=True,
)
def set_edit_index(edit_clicks, current):
    for i, n in enumerate(edit_clicks):
        if n:
            return i
    return current


# ---- Save / Cancel edited project (ALL-based handler) ----
@app.callback(
    Output("projects-store", "data", allow_duplicate=True),
    Output("edit-project-store", "data", allow_duplicate=True),
    Input({"type": "save-edit-project", "index": ALL}, "n_clicks"),
    Input({"type": "cancel-edit-project", "index": ALL}, "n_clicks"),
    State({"type": "edit-project-name", "index": ALL}, "value"),
    State({"type": "edit-project-description", "index": ALL}, "value"),
    State({"type": "edit-project-goal", "index": ALL, "goal": ALL}, "value"),
    State("goals-store", "data"),
    State("projects-store", "data"),
    prevent_initial_call=True,
)
def save_or_cancel_edit(save_clicks, cancel_clicks, names, descs, goal_values, goals, projects):
    projects = projects or []
    # no input -> nothing
    if not (save_clicks or cancel_clicks):
        return dash.no_update, dash.no_update

    trigger = ctx.triggered_id
    if not trigger or not isinstance(trigger, dict):
        return dash.no_update, dash.no_update

    idx = trigger.get("index")
    if idx is None or idx >= len(projects):
        return dash.no_update, dash.no_update

    # If cancel clicked -> clear edit index
    if trigger.get("type") == "cancel-edit-project":
        return projects, None

    # If save clicked -> update project
    if trigger.get("type") == "save-edit-project":
        contribs = {}
        # Normalize goal_values for index:
        normalized = None
        if isinstance(goal_values, list) and len(goal_values) > 0 and isinstance(goal_values[0], list):
            if idx < len(goal_values):
                normalized = goal_values[idx]
        else:
            normalized = goal_values

        if goals and normalized:
            for g, val in zip(goals, normalized):
                contribs[g["name"]] = float(val or 0)

        # names and descs are lists aligned with ALL indexes
        new_name = names[idx] if isinstance(names, list) and idx < len(names) else projects[idx]["name"]
        new_desc = descs[idx] if isinstance(descs, list) and idx < len(descs) else projects[idx].get("description", "")

        projects[idx] = {"name": new_name, "description": new_desc or "", "contributions": contribs}
        return projects, None

    return dash.no_update, dash.no_update


# ---- Render dashboard (shows edit form inline when edit-project-store is set) ----
@app.callback(
    Output("dashboard-content", "children"),
    Input("goals-store", "data"),
    Input("projects-store", "data"),
    Input("edit-project-store", "data"),
)
def render_dashboard(goals, projects, edit_index):
    goals = goals or []
    projects = projects or []

    if not goals:
        return html.Div("➕ Begin met het toevoegen van doelen.", style={"fontSize": "18px"})

    # build a quick lookup for goal units by name
    goal_unit_map = {g["name"]: (g.get("unit", "") or "") for g in goals}

    # Goals with narrower delete buttons (keeps gauge width)
    goal_cards = []
    for i, g in enumerate(goals):
        total_contrib = sum(p["contributions"].get(g["name"], 0) for p in projects)
        target = float(g["target"])
        unit = g.get("unit", "") or ""
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=total_contrib,
            number={"suffix": f" / {target} {unit}".strip()},
            gauge={"axis": {"range": [0, max(target, total_contrib)]}, "bar": {"color": "#28A745" if total_contrib >= target else "#007BFF"}},
            title={"text": f"{g['name']}" + (f" ({unit})" if unit else "")},
        ))
        fig.update_layout(height=250, margin=dict(l=10, r=10, t=40, b=10))

        goal_cards.append(
            html.Div(
                [
                    dcc.Graph(figure=fig, style={"width": "340px", "height": "260px"}),
                    html.Button("❌ Verwijder doel", id={"type": "delete-goal-btn", "index": i}, n_clicks=0,
                                style={"background": "#dc3545", "color": "white", "fontSize": "12px", "padding": "6px 8px", "width": "140px", "margin": "6px auto", "display": "block"}),
                ],
                style={"width": "340px", "textAlign": "center"},
            )
        )

    # Projects: show inline edit form if edit_index == i, otherwise show details with edit/delete
    project_cards = []
    for i, p in enumerate(projects):
        if edit_index is not None and i == edit_index:
            # show edit form for project i
            goal_inputs = []
            for g in goals:
                unit = g.get("unit", "") or ""
                goal_inputs.append(
                    html.Div(
                        [
                            html.Label(f"Bijdrage aan {g['name']} ({unit})"),
                            dcc.Input(id={"type": "edit-project-goal", "index": i, "goal": g["name"]},
                                      type="number", value=p["contributions"].get(g["name"], 0),
                                      style={"marginLeft": "10px", "width": "120px"}),
                        ],
                        style={"marginBottom": "8px"},
                    )
                )

            project_cards.append(
                html.Div(
                    [
                        html.H4(f"Project bewerken: {p['name']}"),
                        dcc.Input(id={"type": "edit-project-name", "index": i}, value=p["name"], type="text", style={"width": "100%", "marginBottom": "8px"}),
                        dcc.Textarea(id={"type": "edit-project-description", "index": i}, value=p.get("description", ""), style={"width": "100%", "height": "100px", "marginBottom": "8px"}),
                        html.Div(goal_inputs),
                        html.Button("Opslaan", id={"type": "save-edit-project", "index": i}, style={"background": "#007BFF", "color": "white", "marginTop": "8px"}),
                        html.Button("Annuleren", id={"type": "cancel-edit-project", "index": i}, style={"marginLeft": "10px", "marginTop": "8px"}),
                    ],
                    style={"border": "1px solid #ddd", "borderRadius": "8px", "padding": "10px", "marginBottom": "8px", "background": "#fffbe6"},
                )
            )
        else:
            contribs_items = []
            for k, v in p["contributions"].items():
                unit = goal_unit_map.get(k, "")
                label = f"{k}: {v}" + (f" {unit}" if unit else "")
                contribs_items.append(html.Li(label))
            contribs = html.Ul(contribs_items)

            project_cards.append(
                html.Details(
                    [
                        html.Summary(p["name"], style={"fontWeight": "bold", "fontSize": "16px", "cursor": "pointer"}),
                        html.Div(
                            [
                                html.P(p["description"] or "Geen beschrijving opgegeven."),
                                contribs,
                                html.Div(
                                    [
                                        html.Button("✏️ Bewerken", id={"type": "edit-project-btn", "index": i}, n_clicks=0, style={"background": "#ffc107", "color": "black", "marginRight": "6px"}),
                                        html.Button("❌ Verwijderen", id={"type": "delete-project-btn", "index": i}, n_clicks=0, style={"background": "#dc3545", "color": "white"}),
                                    ]
                                ),
                            ],
                            style={"marginLeft": "15px", "marginBottom": "10px"},
                        ),
                    ],
                    style={"border": "1px solid #ddd", "borderRadius": "8px", "padding": "10px", "marginBottom": "8px", "background": "#f9f9f9"},
                )
            )

    return html.Div(
        [
            html.Div(goal_cards, style={"display": "flex", "gap": "15px", "flexWrap": "wrap", "marginBottom": "15px"}),
            html.Hr(style={"marginTop": "10px", "marginBottom": "10px"}),
            html.H3("Projecten", style={"marginBottom": "8px"}),
            html.Div(project_cards or [html.P("Nog geen projecten toegevoegd.")]),
        ]
    )


# Auto-open browser
def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050/")


if __name__ == "__main__":
    Timer(1, open_browser).start()
    app.run(debug=True)
