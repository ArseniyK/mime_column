import gtk
import os
from plugins.file_list.plugin import Column, FileList
from plugin_base.column_extension import ColumnExtension

def register_plugin(application):
	"""Register plugin class with application"""
	application.register_column_extension(FileList, TypeColumn)

class TypeColumn(ColumnExtension):
	"""Base class for extending owner and group for item list"""

	def __init__(self, parent, store):
		ColumnExtension.__init__(self, parent, store)
		self._column_id = len(Column.__dict__)-2
		self._parent = parent
		self._associations_manager = self._parent._parent.associations_manager
		self._create_column()
		self._model = {}

		# Monkey patch
		store_clear = store.clear

		def clear():
			store_clear()
			self._model = {}
			return

		store.clear = clear

	def __set_cell_data(self, column, cell, store, selected_iter, data=None):
		"""Set column value"""

		is_parent = store.get_value(selected_iter, Column.IS_PARENT_DIR)
		mime_type = ''

		if not is_parent:
			iter = store.get_value(selected_iter, Column.NAME)
			mime_type = self._model.get(iter)
			if mime_type is None:
				path = os.path.join(self._parent.path, store.get_value(selected_iter, Column.NAME))
				# get content type
				if self._parent._provider.is_dir(path):
					mime_type = 'inode/directory'

				else:
					mime_type = self._associations_manager.get_mime_type(path)

					# content type is unknown, try to detect using content
					try:
						if self._associations_manager.is_mime_type_unknown(mime_type):

							data = self._associations_manager.get_sample_data(path, self._parent._provider)
							mime_type = self._associations_manager.get_mime_type(data=data)
					except Exception:
						pass
				self._model.update({iter: mime_type})

		cell.set_property('text', mime_type)

	def _create_column(self):
		"""Create column"""
		self._cell_renderer = gtk.CellRendererText()
		self._parent.set_default_font_size(self._get_column_name(), 8)

		self._column = gtk.TreeViewColumn(self._get_column_title())
		self._column.pack_start(self._cell_renderer, True)
		self._column.set_data('name', self._get_column_name())
		self._column.set_cell_data_func(self._cell_renderer, self.__set_cell_data, self._store)
		self._column._connect = self._column.connect
		self._column.connect = lambda *args: None
		self._column._connect('clicked', self._set_sort_function, self._column_id)

	def _set_sort_function(self, widget, data=None):

		if widget is not self._parent._sort_column_widget:
			self._parent._sort_column_widget = widget

		if data is not None:
			if self._parent._sort_column == data:
				# reverse sorting if column is already sorted
				self._parent._sort_ascending = not self._parent._sort_ascending

			else:
				# set sorting column
				self._parent._sort_column = data

		self._apply_sort_function()

	def _apply_sort_function(self, focus_selected=True):
		"""Apply sort settings"""
		# set sort indicator only on one column
		for column in self._parent._columns:
			selected = column is self._parent._sort_column_widget
			column.set_sort_indicator(selected)

		# apply sorting function
		order = [gtk.SORT_DESCENDING, gtk.SORT_ASCENDING][self._parent._sort_ascending]
		self._parent._sort_column_widget.set_sort_order(order)

		self._store.set_sort_func(self._parent._sort_column, self._sort_list)
		self._store.set_sort_column_id(self._parent._sort_column, order)

		if focus_selected:
			selection = self._parent._item_list.get_selection()
			item_list, iter_to_scroll = selection.get_selected()
			if iter_to_scroll:
				path_to_scroll = item_list.get_path(iter_to_scroll)
				self._parent._item_list.scroll_to_cell(path_to_scroll, None, True, 0.5)

	def _sort_list(self, item_list, iter1, iter2, data=None):
		"""Compare two items for sorting process"""
		reverse = (1, -1)[self._parent._sort_ascending]

		iter = item_list.get_value(iter1, Column.NAME)
		value1 = self._model.get(iter)
		iter = item_list.get_value(iter2, Column.NAME)
		value2 = self._model.get(iter)

		item1 = (
				reverse * item_list.get_value(iter1, Column.IS_PARENT_DIR),
				reverse * item_list.get_value(iter1, Column.IS_DIR),
				value1
			)

		item2 = (
				reverse * item_list.get_value(iter2, Column.IS_PARENT_DIR),
				reverse * item_list.get_value(iter2, Column.IS_DIR),
				value2
			)

		return cmp(item1, item2)

	def _get_column_name(self):
		"""Returns column name"""
		return 'type'

	def _get_column_title(self):
		"""Returns column title"""
		return _('Type')

	def get_sort_column(self):
		"""Return sort column"""
		return None
