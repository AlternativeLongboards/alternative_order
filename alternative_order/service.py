from kivy.app import App
from datetime import datetime
from api_service import ApiService
import settings

class AppService:
    def __init__(self, my_app):
        self.api = ApiService()
        self.my_app = my_app
        self.current_worker = ''
        self.workers = {}
        self.current_order_boards = {}
        self.readed_order = {}
        self.current_order = 0
        self.current_boards = []
        self.init_values()

    def init_values(self):
        workers_raw_data = self.api.get_endpoint_data('workers')

        self.my_app.main_app_name_label = '{} ROOM'.format(settings.STATION_NAME)
        self.my_app.status_label = 'connected'

        self.workers = {worker['barcode']: worker['username'] for 
                        worker in workers_raw_data}

    def update_worker(self, _barcode):
        if _barcode in self.workers:
            if self.current_worker is '':
                self.current_worker = self.workers[_barcode]
                self.my_app.worker_label = self.current_worker
                self.my_app.status_label = 'welcome'
            else:
                self.current_worker = ''
                self.my_app.worker_label = 'no worker'
                self.my_app.status_label = '-'
            return True
        return False

    def update_barcode_list(self, _data):
        current_last_barcode_label = self.my_app.last_barcode_label
        self.my_app.last_barcode_label = str(_data)

        for index in range(10, 1, -1):
            up_label = getattr(self.my_app, 'barcode_label_{}'.format(index - 1))
            setattr(self.my_app, 'barcode_label_{}'.format(index), up_label)

        if current_last_barcode_label != '':
            first_history_label = '{} {}'.format(datetime.now().strftime('%H:%M:%S'),
                                                 current_last_barcode_label)
        else:
            first_history_label = ''

        self.my_app.barcode_label_1 = first_history_label
        self.my_app.last_time_label = datetime.now().strftime('%H:%M:%S')

    def add_barcode(self, _barcode):
        if self.current_order == 0:
            self.my_app.status_label = 'READ ORDER'
            return False
        
        message = self.api.get_endpoint_data(_endpoint_string='boards/{}'.format(_barcode))
        if not bool(message):
            self.my_app.status_label = 'INVALID BARCODE'
            return False

        model_count = self.current_order_boards.get(message['model'], False)
        if not model_count:
            self.my_app.status_label = 'NOT IN ORDER'
            return False

        if model_count > 0:
            self.current_boards.append(_barcode)
            self.current_order_boards[message['model']] = model_count - 1
            self.my_app.status_label = 'ADDED'
        else:
            self.my_app.status_label = 'MODEL FULL'

    def check_new_order_available(self):
        order_number = self.my_app.order_id
        if order_number != self.current_order:
            self.current_order = order_number
            self.load_order(order_number)

    def load_order(self, _id):
        order = self.api.get_endpoint_data("orders/{}".format(_id))
        boards = order.get('boards', False)
        if boards:
            self.current_order_boards = boards
            self.readed_order = boards
            self.my_app.status_label = 'ORDER LOADED'
            self.my_app.order_detail_label = order['client']
            self.create_message_list()
        else:
            self.my_app.status_label = 'NO ORDER'
            self.my_app.order_detail_label = ''
            self.my_app.order_number_texbox.text = 'chuj'

    def create_message_list(self):
        self.my_app.message_labels = []
        index = 0
        for board, qty in self.readed_order.items():
            free_space = ' '*(20 - len(board))
            label_value = '{}:{}{}       {}    <--- LEFT'.format(board,free_space, 
                                                            qty,
                                                            self.current_order_boards[board])
            self.my_app.message_labels.append(label_value)
            index = index + 1

    def main_handling(self, _barcode):
        if _barcode != 0:
            if not self.update_worker(_barcode):
                if not self.current_worker == "":
                    self.add_barcode(_barcode)
                    self.create_message_list()
                else:
                    self.my_app.status_label = 'SCAN WORKER CARD'
            self.update_barcode_list(_barcode)