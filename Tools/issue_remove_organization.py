"""
Temporary script to simulate the issue with removing an organization.
"""

# import logging
from competition import neostore
from lib import my_env

if __name__ == "__main__":
    my_env.init_loghandler(__file__, "c:\\temp\\log", "debug")
    ns = neostore.NeoStore()
    # org_id = "7661543a-0d12-47da-aff2-8c71730171f2"
    ns.clear_locations()
