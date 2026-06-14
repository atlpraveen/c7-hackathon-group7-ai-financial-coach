def synthesizer_node(state):
    return {
        'status': 'success',
        'recommendations': state.get('results', {})
    }
