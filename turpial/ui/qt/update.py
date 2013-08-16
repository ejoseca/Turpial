# -*- coding: utf-8 -*-

# Qt update box for Turpial

from PyQt4.QtGui import QFont
from PyQt4.QtGui import QIcon
from PyQt4.QtGui import QLabel
from PyQt4.QtGui import QWidget
from PyQt4.QtGui import QComboBox
from PyQt4.QtGui import QTextEdit
from PyQt4.QtGui import QCompleter
from PyQt4.QtGui import QPushButton
from PyQt4.QtGui import QTextCursor
from PyQt4.QtGui import QVBoxLayout, QHBoxLayout

from PyQt4.QtCore import Qt

from turpial.ui.lang import i18n
from turpial.ui.qt.loader import BarLoadIndicator
from turpial.ui.qt.widgets import ImageButton, ToggleButton

from libturpial.common import get_username_from, get_protocol_from

MAX_CHAR = 140

class UpdateBox(QWidget):
    def __init__(self, base):
        QWidget.__init__(self)
        self.base = base
        self.showed = False
        self.setWindowTitle(i18n.get('whats_happening'))
        self.setFixedSize(500, 120)
        #self.setWindowFlags(Qt.Window | Qt.WindowTitleHint | Qt.WindowCloseButtonHint | Qt.CustomizeWindowHint)

        completer = QCompleter(['one', 'two', 'carlos', 'maria',
            'ana', 'carolina', 'alberto', 'pedro', 'tomas'])

        self.text_edit = CompletionTextEdit()
        self.text_edit.setCompleter(completer)

        self.upload_button = ImageButton(base, 'action-upload.png',
                i18n.get('upload_image'))
        self.short_button = ImageButton(base, 'action-shorten.png',
                i18n.get('short_urls'))

        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.char_count = QLabel('140')
        self.char_count.setFont(font)

        self.update_button = QPushButton(i18n.get('update'))

        self.accounts_combo = QComboBox()
        accounts = self.base.get_registered_accounts()
        for account in accounts:
            protocol = get_protocol_from(account.id_)
            icon = QIcon(base.get_image_path('%s.png' % protocol))
            self.accounts_combo.addItem(icon, get_username_from(account.id_), account.id_)
        icon = QIcon(base.get_image_path('action-conversation.png'))
        self.accounts_combo.addItem(icon, i18n.get('broadcast'), 'broadcast')

        buttons = QHBoxLayout()
        buttons.addWidget(self.accounts_combo)
        buttons.addWidget(self.upload_button)
        buttons.addWidget(self.short_button)
        buttons.addStretch(0)
        buttons.addWidget(self.char_count)
        buttons.addWidget(self.update_button)

        self.loader = BarLoadIndicator()
        self.loader.setVisible(False)

        self.error_message = QLabel()

        self.update_button.clicked.connect(self.__update_status)
        self.text_edit.textChanged.connect(self.__update_count)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit, 1)
        layout.addWidget(self.loader)
        layout.addLayout(buttons)
        layout.setContentsMargins(5, 5, 5, 5)
        self.setLayout(layout)


    def __count_chars(self):
        message = self.text_edit.toPlainText()
        return MAX_CHAR - len(message)

    def __update_count(self):
        remaining_chars = self.__count_chars()
        if remaining_chars <= 10:
            self.char_count.setStyleSheet("QLabel { color: #D40D12 }")
        elif remaining_chars > 10 and remaining_chars <= 20:
            self.char_count.setStyleSheet("QLabel { color: #D4790D }")
        else:
            self.char_count.setStyleSheet("QLabel { color: #000000 }")
        self.char_count.setText(str(remaining_chars))

    def __update_status(self):
        index = self.accounts_combo.currentIndex()
        account_id = str(self.accounts_combo.itemData(index).toPyObject())
        message = self.text_edit.toPlainText()

        if len(message) == 0:
            print i18n.get('you_can_not_submit_an_empty_message')
            return

        #if len(message) > MAX_CHAR:
        #    self.message.set_error_text(i18n.get('message_looks_like_testament'))
        #    return
        self.enable(False)
        self.base.update_status(account_id, message)

    def __clear(self):
        self.text_edit.setText('')
        self.accounts_combo.setIndex(0)

    def __reset(self):
        pass

    def closeEvent(self, event):
        event.ignore()
        self.hide()

    def enable(self, value):
        self.text_edit.setEnabled(value)
        self.accounts_combo.setEnabled(value)
        self.upload_button.setEnabled(value)
        self.short_button.setEnabled(value)
        self.update_button.setEnabled(value)
        self.loader.setVisible(not value)

    def done(self):
        self.__clear()
        self.__reset()
        self.hide()

class CompletionTextEdit(QTextEdit):
    IGNORED_KEYS = (
        Qt.Key_Enter,
        Qt.Key_Return,
        Qt.Key_Escape,
        Qt.Key_Tab,
        Qt.Key_Backtab
    )

    def __init__(self):
        QTextEdit.__init__(self)
        self.completer = None

    def setCompleter(self, completer):
        if self.completer:
            self.disconnect(self.completer, 0, self, 0)

        self.completer = completer
        self.completer.setWidget(self)
        self.completer.activated.connect(self.insertCompletion)

    def insertCompletion(self, completion):
        if self.completer.widget() != self:
            return

        tc = self.textCursor()
        extra = (completion.length() - self.completer.completionPrefix().length())
        tc.movePosition(QTextCursor.Left)
        tc.movePosition(QTextCursor.EndOfWord)
        tc.insertText(completion.right(extra))
        self.setTextCursor(tc)

    def textUnderCursor(self):
        tc = self.textCursor()
        text = ""
        while True:
            tc.movePosition(QTextCursor.Left, QTextCursor.KeepAnchor)
            text = tc.selectedText()
            if tc.position() == 0:
                break
            if text.startsWith(' '):
                text = text[1:]
                break

        return text

    def focusInEvent(self, event):
        if self.completer:
            self.completer.setWidget(self)
        QTextEdit.focusInEvent(self, event)

    def keyPressEvent(self, event):
        if self.completer and self.completer.popup().isVisible():
            if event.key() in self.IGNORED_KEYS:
                event.ignore()
                return

        QTextEdit.keyPressEvent(self, event)

        hasModifier = event.modifiers() != Qt.NoModifier

        completionPrefix = self.textUnderCursor()

        if hasModifier or event.text().isEmpty() or not completionPrefix.startsWith('@'):
            self.completer.popup().hide()
            return

        if completionPrefix.startsWith('@') and completionPrefix[1:] != self.completer.completionPrefix():
            self.completer.setCompletionPrefix(completionPrefix[1:])
            popup = self.completer.popup()
            popup.setCurrentIndex(self.completer.completionModel().index(0, 0))

        cursor_rect = self.cursorRect()
        cursor_rect.setWidth(self.completer.popup().sizeHintForColumn(0) 
                + self.completer.popup().verticalScrollBar().sizeHint().width())
        self.completer.complete(cursor_rect)

