def serialize_section(section):
    """Turn a SlideSection into the dict the frontend expects, including its parameters."""
    pset = section.parameter_sets.first()
    return {
        'id': section.id,
        'view_type': section.view_type,
        'width_fraction': section.width_fraction,
        'content': section.content,
        'content_path': section.content_path,
        'mode': section.mode,
        'url_pattern': section.url_pattern,
        'parameters': serialize_parameters(pset),
        'properties': section.properties
    }
    
# Helper to coerce default values based on parameter type 
def coerce_default(ptype, raw):
    if raw == '' or raw is None:
        return None
    if ptype == 'number':
        return float(raw)
    if ptype == 'boolean':
        return str(raw).lower() == 'true'
    return raw

def serialize_parameters(pset):
    """Turn a ParameterSet into the name-keyed dict the frontend expects."""
    params = {}
    if pset:
        for p in pset.parameters.all():
            params[p.name] = {
                'id': p.id,
                'type': p.ptype,
                'description': p.description,
                'range': {'min': p.minimum, 'max': p.maximum} if p.ptype == 'number' else None,
                'default': coerce_default(p.ptype, p.default),
                'options': p.options,
            }
    return params
        