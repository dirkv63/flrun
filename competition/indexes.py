from .models_sql import graph

nodes = [
    ('Person', 'name'),
    ('Organization', 'name')
]

for label, property in nodes:
    try:
        graph.schema.create_uniqueness_constraint(label,property)
    except:
        continue