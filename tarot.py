from os import listdir
from random import shuffle, randint
from PIL import Image
from tempfile import NamedTemporaryFile
from telegram import Update
from telegram.ext import CallbackContext
import db
import re


class Tarot:
    def __init__(self):
        self.card_data = db.readSelitykset()

    def make_image(self, reading):
        reading_image = Image.new('RGB', (250 * len(reading), 429))

        for i in range(len(reading)):
            # chance for flipped card
            if randint(0, 10) == 0:
                card_image = Image.open("resources/tarot/" + reading[i])
                image_flipped = card_image.transpose(Image.FLIP_TOP_BOTTOM)
                reading_image.paste(im=image_flipped, box=(250 * i, 0))
            # normal card
            else:
                reading_image.paste(im=Image.open("resources/tarot/" + reading[i]), box=(250 * i, 0))

        # do NamedTempFile because Linux and Windows require completely different methods for this
        # the old Win method of making a non-delete file and then deleting it borks on Linux
        # this will bork on Windows but who cares
        fp = NamedTemporaryFile()
        fp.seek(0)
        reading_image.save(fp, 'jpeg', quality=75)
        return fp

    def draw_cards(self, amount):
        # cards in resources folder
        cards = listdir("resources/tarot")
        # magic shuffling
        shuffle(cards)
        # add spookiness as requested, shuffle more
        shuffle(cards)
        shuffle(cards)
        reading = []
        for i in range(amount):
            # how 2 reverse a queue
            reading.append(cards.pop())

        # return the temp file with the image
        return self.make_image(reading)

    def get_reading(self, update: Update, context: CallbackContext):
        try:
            size = int(update.message.text.lower().split(' ')[1])
        except ValueError:
            context.bot.sendMessage(chat_id=update.message.chat_id, text=":--D")
            return

        if size < 1 or size > 78:
            context.bot.sendMessage(chat_id=update.message.chat_id, text=":--D")
            return
        image_file = self.draw_cards(size)
        image_file.seek(0)
        if size > 10:
            context.bot.sendDocument(chat_id=update.message.chat_id, document=open(image_file.name, 'rb'))
        else:
            context.bot.send_photo(chat_id=update.message.chat_id, photo=open(image_file.name, 'rb'))
        image_file.close()

    def explain_card(self, text):
        explanations = ""

        for datum in self.card_data:
            name = datum[0].lower()
            if name in text:
                for rev_keyword in ["reversed", "ylösalaisin", "väärinpäin"]:
                    if rev_keyword + " " + name in text or name + " " + rev_keyword in text:
                        explanation = datum[2]
                        explanations += "Reversed " + name + ": " + explanation + "\n\n"
                    else:
                        explanation = datum[1]
                        explanations += name + ": " + explanation + "\n\n"

        return explanations

    def get_explanation(self, update: Update, context: CallbackContext):
        message = self.explain_card(update.message.text.lower())
        if message != "":
            context.bot.sendMessage(chat_id=update.message.chat_id, text=message)

    def messageHandler(self, update: Update, context: CallbackContext):
        msg = update.message
        text = msg.text.lower()
        if text is not None:
            if re.match(r'^/tarot [0-9]+(?!\S)', text):
                self.get_reading(update, context)
            elif "selitä" in text or "selitys" in text:
                self.get_explanation(update, context)

    def getCommands(self):
        return dict()
