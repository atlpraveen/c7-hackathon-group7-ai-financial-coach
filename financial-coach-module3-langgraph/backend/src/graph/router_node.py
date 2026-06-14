def router_node(state):
    query = state.get('query', '').lower()
    tasks = []

    if 'debt' in query:
        tasks.append('debt')
    if 'save' in query:
        tasks.append('savings')
    if 'budget' in query:
        tasks.append('budget')
    if 'invest' in query:
        tasks.append('investment')

    state['tasks'] = tasks
    return state
