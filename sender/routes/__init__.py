import os

router_files = [f[:-3] for f in os.listdir(os.path.dirname(__file__)) if f.endswith('.py') and f != '__init__.py']

routers = []
for router_file in router_files:
    module = __import__(f'routes.{router_file}', fromlist=['router'])
    routers.append(module.router)
