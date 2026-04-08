from app.models import Setting

def get_all_settings(as_dict=True):
    settings = Setting.query.all()
    if as_dict:
        return {s.function_desc: s.function for s in settings}
    return settings
