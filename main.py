import os
import pandas as pd
import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc
from datetime import datetime

from agent.graph import HealthcareAgent

# Initialize Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Healthcare AI Assistant"

# Global variable to store streaming state
streaming_state = {}

def streaming_callback(state):
    """Callback function to handle streaming updates"""
    streaming_state['current'] = state

# Initialize the agent with streaming callback
agent = HealthcareAgent(streaming_callback=streaming_callback)

# Load user data
try:
    users_df = pd.read_csv('data/user.csv')
    user_options = [
        {'label': f"{row['display_name']} ({row['role']})", 'value': str(row['user_id'])}
        for _, row in users_df.iterrows()
    ]
except Exception as e:
    print(f"Error loading users: {e}")
    user_options = [{'label': 'Demo User', 'value': '101'}]

# Store for conversation history (in production, use Redis or database)
conversation_store = {}

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("🏥 Healthcare AI Assistant", className="text-center mb-4"),
            html.Hr()
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Select User"),
                dbc.CardBody([
                    dcc.Dropdown(
                        id='user-dropdown',
                        options=user_options,
                        value='101',  # Default to first user
                        placeholder="Select a user...",
                        className="mb-3"
                    ),
                    html.Div(id='user-info', className="text-muted")
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5("Conversation", className="mb-0"),
                    dbc.Button("Clear Chat", id="clear-button", color="outline-secondary", size="sm")
                ], className="d-flex justify-content-between align-items-center"),
                dbc.CardBody([
                    html.Div(
                        id='chat-history',
                        style={
                            'height': '400px',
                            'overflow-y': 'auto',
                            'border': '1px solid #dee2e6',
                            'border-radius': '0.375rem',
                            'padding': '15px',
                            'background-color': '#f8f9fa'
                        }
                    )
                ])
            ])
        ], width=12)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.InputGroup([
                        dbc.Input(
                            id='message-input',
                            placeholder="Ask me about your healthcare plan, doctors, coverage, costs...",
                            type="text",
                            style={'border-radius': '20px 0 0 20px'}
                        ),
                        dbc.Button(
                            "Send", 
                            id="send-button",
                            color="primary",
                            n_clicks=0,
                            style={'border-radius': '0 20px 20px 0'}
                        )
                    ])
                ])
            ])
        ], width=12)
    ]),
    
    # Loading and streaming indicator
    dbc.Row([
        dbc.Col([
            html.Div(id="streaming-status", style={'display': 'none'}),
            dcc.Interval(
                id='streaming-interval',
                interval=500,  # Update every 500ms
                n_intervals=0,
                disabled=True
            )
        ])
    ]),
    
    # Store components for state management
    dcc.Store(id='conversation-store', data={}),
    dcc.Store(id='current-user-store', data='101')
    
], fluid=True, style={'max-width': '800px', 'margin': '0 auto', 'padding': '20px'})

# Callback to update user info
@app.callback(
    Output('user-info', 'children'),
    Output('current-user-store', 'data'),
    Input('user-dropdown', 'value')
)
def update_user_info(selected_user):
    if not selected_user:
        return "No user selected", None
    
    try:
        user_row = users_df[users_df['user_id'] == int(selected_user)]
        if not user_row.empty:
            user = user_row.iloc[0]
            info_text = f"Role: {user['role']} | Location: {user['city']}, {user['state']}"
            return info_text, selected_user
    except Exception as e:
        print(f"Error getting user info: {e}")
    
    return f"User ID: {selected_user}", selected_user

# Callback to enable streaming when processing starts
@app.callback(
    Output('streaming-interval', 'disabled', allow_duplicate=True),
    Input('send-button', 'n_clicks'),
    Input('message-input', 'n_submit'),
    State('message-input', 'value'),
    prevent_initial_call=True
)
def enable_streaming(send_clicks, input_submit, message):
    ctx = callback_context
    if not ctx.triggered or not message or not message.strip():
        return True
    
    # Enable streaming when a message is sent
    return False

# Callback for streaming updates
@app.callback(
    Output('streaming-status', 'children'),
    Output('streaming-interval', 'disabled'),
    Input('streaming-interval', 'n_intervals'),
    State('streaming-interval', 'disabled')
)
def update_streaming_status(n_intervals, disabled):
    if disabled or 'current' not in streaming_state:
        return "", True
    
    current_state = streaming_state['current']
    if not current_state.processing_steps:
        return "", True
    
    latest_step = current_state.processing_steps[-1]
    if latest_step['status'] == 'completed' and latest_step['step'] == 'finalize':
        return "", True  # Processing complete, hide streaming
    
    # Create streaming status display
    status_content = dbc.Alert([
        html.Div([
            dbc.Spinner(size="sm", className="me-2"),
            latest_step['description']
        ], className="d-flex align-items-center")
    ], color="info", className="mb-2")
    
    return status_content, False

# Callback to handle sending messages
@app.callback(
    Output('chat-history', 'children'),
    Output('message-input', 'value'),
    Output('conversation-store', 'data'),
    Output('streaming-interval', 'disabled', allow_duplicate=True),
    Input('send-button', 'n_clicks'),
    Input('message-input', 'n_submit'),
    Input('clear-button', 'n_clicks'),
    State('message-input', 'value'),
    State('current-user-store', 'data'),
    State('conversation-store', 'data'),
    prevent_initial_call=True
)
def handle_message(send_clicks, input_submit, clear_clicks, message, current_user, conversation_data):
    ctx = callback_context
    
    if not ctx.triggered:
        return [], "", {}, True
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Handle clear button
    if button_id == 'clear-button' and clear_clicks:
        return [], "", {}, True
    
    # Handle send message
    if button_id in ['send-button', 'message-input'] and message and message.strip():
        if not current_user:
            error_bubble = create_error_bubble("Please select a user first.")
            return [error_bubble], "", conversation_data, True
        
        # Get conversation history for this user
        user_conversations = conversation_data.get(current_user, [])
        
        # Add user message to history
        timestamp = datetime.now().strftime("%H:%M")
        user_bubble = create_user_bubble(message, timestamp)
        user_conversations.append({
            'type': 'user',
            'message': message,
            'timestamp': timestamp
        })
        
        try:
            # Clear previous streaming state and start streaming updates
            streaming_state.clear()
            # Enable streaming interval - this will be handled by a separate callback
            result = agent.process_query(
                user_id=current_user,
                user_message=message,
                conversation_history=user_conversations
            )
            
            # Create bot response
            bot_timestamp = datetime.now().strftime("%H:%M")
            bot_response = result.final_answer or "I'm sorry, I couldn't process your request."
            references = result.references or []
            
            bot_bubble = create_bot_bubble(bot_response, references, bot_timestamp)
            
            # Add bot message to history
            user_conversations.append({
                'type': 'bot',
                'message': bot_response,
                'references': references,
                'timestamp': bot_timestamp,
                'confidence': result.confidence_score
            })
            
        except Exception as e:
            print(f"Error processing message: {e}")
            bot_bubble = create_error_bubble(f"Error: {str(e)}")
            user_conversations.append({
                'type': 'error',
                'message': f"Error: {str(e)}",
                'timestamp': datetime.now().strftime("%H:%M")
            })
        
        # Update conversation store
        conversation_data[current_user] = user_conversations
        
        # Generate chat bubbles
        chat_bubbles = []
        for msg in user_conversations:
            if msg['type'] == 'user':
                chat_bubbles.append(create_user_bubble(msg['message'], msg['timestamp']))
            elif msg['type'] == 'bot':
                chat_bubbles.append(create_bot_bubble(
                    msg['message'], 
                    msg.get('references', []), 
                    msg['timestamp']
                ))
            elif msg['type'] == 'error':
                chat_bubbles.append(create_error_bubble(msg['message']))
        
        return chat_bubbles, "", conversation_data, True  # Disable streaming when done
    
    # Load existing conversation when switching users
    if current_user and current_user in conversation_data:
        user_conversations = conversation_data[current_user]
        chat_bubbles = []
        for msg in user_conversations:
            if msg['type'] == 'user':
                chat_bubbles.append(create_user_bubble(msg['message'], msg['timestamp']))
            elif msg['type'] == 'bot':
                chat_bubbles.append(create_bot_bubble(
                    msg['message'], 
                    msg.get('references', []), 
                    msg['timestamp']
                ))
            elif msg['type'] == 'error':
                chat_bubbles.append(create_error_bubble(msg['message']))
        return chat_bubbles, "", conversation_data, True
    
    return [], "", conversation_data, True

def create_user_bubble(message, timestamp):
    """Create a user message bubble."""
    return html.Div([
        html.Div([
            html.Div(message, className="mb-1"),
            html.Small(timestamp, className="text-muted")
        ], className="p-3 bg-primary text-white rounded-3", 
           style={'max-width': '70%', 'margin-left': 'auto', 'word-wrap': 'break-word'})
    ], className="d-flex justify-content-end mb-3")

def create_bot_bubble(message, references, timestamp):
    """Create a bot response bubble with references."""
    bubble_content = [
        html.Div(message, className="mb-2"),
    ]
    
    # Add references if available
    if references:
        reference_items = []
        for i, ref in enumerate(references, 1):
            reference_items.append(html.Li(ref, className="small text-muted"))
        
        bubble_content.extend([
            html.Hr(className="my-2"),
            html.Strong("References:", className="small text-muted"),
            html.Ul(reference_items, className="mb-1 ps-3")
        ])
    
    bubble_content.append(html.Small(timestamp, className="text-muted"))
    
    return html.Div([
        html.Div(
            bubble_content,
            className="p-3 bg-light border rounded-3",
            style={'max-width': '70%', 'word-wrap': 'break-word'}
        )
    ], className="d-flex justify-content-start mb-3")

def create_error_bubble(error_message):
    """Create an error message bubble."""
    return html.Div([
        html.Div([
            html.I(className="fas fa-exclamation-triangle me-2"),
            error_message
        ], className="p-3 bg-danger text-white rounded-3 d-flex align-items-center",
           style={'max-width': '70%', 'word-wrap': 'break-word'})
    ], className="d-flex justify-content-center mb-3")

# Enable Enter key for sending messages
app.clientside_callback(
    """
    function(n_submit) {
        return n_submit;
    }
    """,
    Output('message-input', 'n_submit'),
    Input('message-input', 'n_submit')
)

if __name__ == '__main__':
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  Warning: OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
    
    print("🚀 Starting Healthcare AI Assistant...")
    print("📋 Features:")
    print("   • Multi-user chat interface") 
    print("   • SQL database queries")
    print("   • PDF document search")
    print("   • Two-layer AI reasoning")
    print("\n🌐 Open your browser to: http://127.0.0.1:8050")
    
    app.run(debug=True, host='127.0.0.1', port=8050)