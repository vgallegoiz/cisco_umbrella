import json
import logging
import sys
from datetime import datetime

import import_declare_test
from solnlib import conf_manager, log
from solnlib.modular_input import checkpointer
from splunklib import modularinput as smi

from umbrellaObject import Umbrella

ADDON_NAME = "cisco_umbrella"

def logger_for_input(input_name: str) -> logging.Logger:
    return log.Logs().get_logger(f"{ADDON_NAME.lower()}_{input_name}")

def get_account_info(session_key: str, account_name: str):
    cfm = conf_manager.ConfManager(
        session_key,
        ADDON_NAME,
        realm=f"__REST_CREDENTIAL__#{ADDON_NAME}#configs/conf-cisco_umbrella_account",
    )
    account_conf_file = cfm.get_conf("cisco_umbrella_account")
    client_secret = account_conf_file.get(account_name).get("client_secret")
    client_id = account_conf_file.get(account_name).get("client_id")
    url = account_conf_file.get(account_name).get("url")
    return client_secret, client_id, url

class Input(smi.Script):
    def __init__(self):
        super().__init__()

    def create_or_return_checkpointer(self):
        session_key = self._input_definition.metadata["session_key"]
        self.checkpoint = checkpointer.KVStoreCheckpointer(f"{ADDON_NAME}_checkpointer", session_key, ADDON_NAME, )

    def get_scheme(self):
        scheme = smi.Scheme("cisco_umbrella")
        scheme.description = "cisco_umbrella input"
        scheme.use_external_validation = True
        scheme.streaming_mode_xml = True
        scheme.use_single_instance = False
        #scheme.add_argument(smi.Argument("name", title="Name", description="Name", required_on_create=True))        
        return scheme

    def validate_input(self, definition: smi.ValidationDefinition):
        return

    def stream_events(self, inputs: smi.InputDefinition, event_writer: smi.EventWriter):
        # inputs.inputs is a Python dictionary object like:
        # {
        #   "cisco_umbrella://<input_name>": {
        #     "account": "<account_name>",
        #     "disabled": "0",
        #     "host": "$decideOnStartup",
        #     "index": "<index_name>",
        #     "interval": "<interval_value>",
        #     "python.version": "python3",
        #   },
        # }
        for input_name, input_item in inputs.inputs.items():
            normalized_input_name = input_name.split("/")[-1]
            logger = logger_for_input(normalized_input_name)

            try:
                session_key = self._input_definition.metadata["session_key"]
                log_level = conf_manager.get_log_level(
                    logger=logger,
                    session_key=session_key,
                    app_name=ADDON_NAME,
                    conf_name=f"{ADDON_NAME}_settings",
                )
                logger.setLevel(log_level)
                log.modular_input_start(logger, normalized_input_name)
                logger.info("Starting checkpointer")
                self.create_or_return_checkpointer()
                
                logger.info("getting account info")
                client_secret, client_id, url = get_account_info(session_key, input_item.get("account"))
                index = input_item.get("index")
                input_types = input_item.get("input_type", "").split('|')
                input_type_log = ",".join(input_types)
                logger.info(f"index={index} input_name={normalized_input_name}")

                logger.info(f"Initializing Umbrella: input_name={normalized_input_name}")
                umbrella = Umbrella(client_id=client_id, client_secret=client_secret, url=url)
                umbrella.get_auth_token()
                
                try:
                    logger.info("Getting checkpointer for allowed,proxied logs")
                    last_checkpoint = self.checkpoint.get(f"{normalized_input_name}_allowed,proxied")
                    start_time = ""
                    if last_checkpoint is None:
                        logger.info("There is no checkpointer on allowed,blocked logs")
                        start_time = int(datetime.now().timestamp() * 1000) - 60 * 1000
                    else:
                        start_time = last_checkpoint              
                    logger.info("Fetching Umbrella Logs...")
                    end_time = int(datetime.now().timestamp() * 1000)
                    '''if "allowed" in input_types:

                        '''
                    '''if "blocked" in input_types:

                        '''
                    '''if "proxied" in input_types:

                        '''
                    response = umbrella.get_report_logs_all(start_time=start_time, end_time=end_time)
                    try:
                        data = response.json()
                    except Exception as e:
                        logger.error(f"No hay JSON, status code = {response.status_code}")
                        raise Exception
                    now = datetime.now().timestamp()
                    if response.status_code == 200:
                        for item in data['data']:
                            item.update({'input_name': normalized_input_name})
                            event = smi.Event(time="%.3f" % now, sourcetype="cisco:umbrella", index=index, source=normalized_input_name)
                            event.stanza = input_name
                            event.data = json.dumps(item, ensure_ascii=False, default=str)
                            event_writer.write_event(event)
                        logger.info("Cisco Umbrella successfully ingested")
                    else:
                        logger.info(f"No 200 code {response.status_code}")
                    self.checkpoint.update(f"{normalized_input_name}_allowed,proxied", end_time)
                    logger.info(f"Checkpointer on {normalized_input_name} and sourcetyepe cisco:umbrella updated")
                except Exception as e:
                    logger.info("Fallo en get response")
                    log.log_exception(logger, e, exc_label=ADDON_NAME ,msg_before=f'client={normalized_input_name}')
                
                log.modular_input_end(logger, normalized_input_name)
            except Exception as e:
                logger.info(f"Error during Cisco Umbrella ingestion {e}")
                log.log_exception(logger, e, exc_label=ADDON_NAME, msg_before="Error during Cisco Umbrella ingestion")


if __name__ == "__main__":
    exit_code = Input().run(sys.argv)
    sys.exit(exit_code)