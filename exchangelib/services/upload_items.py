from .common import EWSAccountService, to_item_id
from ..properties import ItemId, ParentFolderId
from ..util import create_element, set_xml_value, add_xml_child, MNS


class UploadItems(EWSAccountService):
    """MSDN: https://docs.microsoft.com/en-us/exchange/client-developer/web-service-reference/uploaditems-operation
    """

    SERVICE_NAME = 'UploadItems'
    element_container_name = f'{{{MNS}}}ItemId'

    def call(self, items):
        # _pool_requests expects 'items', not 'data'
        return self._elems_to_objs(self._chunked_get_elements(self.get_payload, items=items))

    def get_payload(self, items):
        """Upload given items to given account.

        'items' is an iterable of tuples where the first element is a Folder instance representing the ParentFolder
        that the item will be placed in and the second element is a tuple containing an optional ItemId, an optional
        Item.is_associated boolean, and a Data string returned from an ExportItems.
        call.

        :param items:
        """
        payload = create_element(f'm:{self.SERVICE_NAME}')
        items_elem = create_element('m:Items')
        payload.append(items_elem)
        for parent_folder, (item_id, is_associated, data_str) in items:
            # TODO: The full spec also allows the "UpdateOrCreate" create action.
            attrs = dict(CreateAction='Update' if item_id else 'CreateNew')
            if is_associated is not None:
                attrs['IsAssociated'] = is_associated
            item = create_element('t:Item', attrs=attrs)
            parent_folder_id = ParentFolderId(parent_folder.id, parent_folder.changekey)
            set_xml_value(item, parent_folder_id, version=self.account.version)
            if item_id:
                set_xml_value(
                    item, to_item_id(item_id, ItemId, version=self.account.version), version=self.account.version
                )
            add_xml_child(item, 't:Data', data_str)
            items_elem.append(item)
        return payload

    def _elems_to_objs(self, elems):
        for elem in elems:
            if isinstance(elem, Exception):
                yield elem
                continue
            yield elem.get(ItemId.ID_ATTR), elem.get(ItemId.CHANGEKEY_ATTR)

    @classmethod
    def _get_elements_in_container(cls, container):
        return [container]
