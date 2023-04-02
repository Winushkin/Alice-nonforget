import pymorphy2
from flask import Flask, request, jsonify

from database_sqlite import Database
from functions import send_help_message, create_buttons
from phrases import get_error_phrase, get_phrase
from states import States
from validators import check_line, words_in_string
from cliche import ADDITION_WORDS

app = Flask(__name__)

database = Database("db.sqlite")

morph = pymorphy2.MorphAnalyzer(lang="ru")

state = States()
states_dict = {}
reminder_template = {}

database.create_database()


@app.route('/post', methods=['POST'])
def main():
    global reminder_template
    data = request.json
    session = data['session']
    version = data['version']
    user_id = session['user']['user_id']
    command = data['request']['command']

    if 'user' not in session.keys():
        answer_response = {
            "response": {
                'text': f"OK",
                'tts': f"OK"
            },
            "session": session,
            "version": version
        }
        return jsonify(answer_response)

    if command in ("стоп", "выход", "выйти", "пока"):
        states_dict[user_id].set_exit()
        answer_response = {
            "response": {
                "text": get_phrase("EXIT", "stop")["text"],
                "tts": get_phrase("EXIT", "stop")["tts"],
                "buttons": []
            },
            "session": session,
            "version": version
        }
        answer_response = create_buttons(*[{"title": "Да", "hide": True},
                                           {"title": "Нет", "hide": True}],
                                         **answer_response)
        states_dict[user_id].set_stage(2)

        return jsonify(answer_response)

    if session['new']:
        database.add_new_user(user_id)
        states_dict[user_id] = States()

        reminder_template[user_id] = {"title": "", "reminder_list": []}
        print(user_id)

        answer_response = {
            "response": {
                'text': get_phrase(states_dict[user_id].get_state(), "zero")['text'],
                'tts': get_phrase(states_dict[user_id].get_state(), "zero")['tts'],
                'buttons': []
            },
            "session": session,
            "version": version
        }
        answer_response = create_buttons(*[{"title": "Создать", "hide": True},
                                           {"title": "Использовать", "hide": True},
                                           {"title": "Удалить", "hide": True},
                                           {"title": "Стоп", "hide": False, }
                                           ], **answer_response)
        return jsonify(answer_response)

    if states_dict[user_id].is_exit(2):
        if command == "да":
            answer_response = {
                "response": get_phrase("EXIT", "bye"),
                "session": session,
                "version": version,
                "end_session": True
            }
            states_dict.pop(user_id)
            return answer_response
        if command == "нет":
            answer_response = {
                "response": {
                    "text": get_phrase("EXIT", "cancel")["text"],
                    "tts": get_phrase("EXIT", "cancel")["tts"],
                    'buttons': []
                },
                "session": session,
                "version": version
            }
            answer_response = create_buttons(*[{"title": "Создать", "hide": True},
                                               {"title": "Использовать", "hide": True},
                                               {"title": "Удалить", "hide": True},
                                               {"title": "Стоп", "hide": False, }
                                               ], **answer_response)
            return jsonify(answer_response)

    if command in ("что ты умеешь", "какие есть команды", "что делать", "команды", "help", "хелп"):
        states_dict[user_id].set_zero()
        return send_help_message(session, version)
    if command == "помощь":
        answer_response = {
            "response": {
                'text': get_phrase("ZERO", "zero")['text'],
                'tts': get_phrase("ZERO", "zero")['tts']
            },
            "session": session,
            "version": version
        }

        return jsonify(answer_response)

    else:
        #  Начальное состояние Алисы
        if not (states_dict[user_id].is_creating() or states_dict[user_id].is_delete() or
                states_dict[user_id].is_using()):
            if command == 'создать':
                states_dict[user_id].set_creating(10)
                answer_response = {

                    "response": {
                        'text': get_phrase(states_dict[user_id].get_state(), "start_message_alt")['text'],
                        'tts': get_phrase(states_dict[user_id].get_state(), "start_message_alt")['tts']
                    },
                    "session": session,
                    "version": version
                }
                return jsonify(answer_response)

            if 'создать' in command:
                reminder_from_user = command.split()
                if len(reminder_from_user) != 1:
                    if 'напоминалк' in command:
                        index = str(command).find('напоминалк')
                        title = command[index + len('напоминалка'):].strip()
                        if database.does_reminder_exists(user_id, title):
                            answer_response = {
                                "response": {
                                    "text": "У вас уже есть напоминалка с таким названием. Придумайте новое",
                                    "tts": "У вас уже есть напоминалка с таким названием. Придумайте новое"
                                },
                                "session": session,
                                "version": version
                            }
                            return answer_response

                        reminder_template[user_id]["title"] = title
                        states_dict[user_id].set_creating()
                        answer_response = {
                            "response": {
                                'text': f"Создала напоминалку с названием {title}. Всё верно?",
                                'tts': f"Создала напоминалку с названием {title}. Всё верно?",
                                'buttons': []
                            },
                            "session": session,
                            "version": version
                        }
                        answer_response = create_buttons(*[{"title": "Да", "hide": True},
                                                           {"title": "Нет", "hide": True}],
                                                         **answer_response)
                        states_dict[user_id].set_creating()
                        return jsonify(answer_response)

            if command == 'использовать':
                states_dict[user_id].set_using(10)
                answer_response = {
                    "response": get_phrase(states_dict[user_id].get_state(), "qwertyuiop"),
                    "session": session,
                    "version": version
                }
                return jsonify(answer_response)

            if 'использовать' in command:
                reminder_from_user = command.split()
                if len(reminder_from_user) != 1:
                    if 'напоминалк' in command:
                        index = str(command).find('напоминалк')
                        title = command[index + len('напоминалка'):].strip()
                        items = database.get_reminder_items(user_id, title)
                        if items:
                            items = items.split(";")
                            reminder_template[user_id] = {}
                            reminder_template[user_id]['title'] = title
                            reminder_template[user_id]['reminder_list'] = items

                            answer_response = {
                                "response": {
                                    'text': f"Напоминалка {reminder_template[user_id]['title']}."
                                            f" Не забудьте: {', '.join(items)}. Мне повторить?",
                                    'tts': f"Напоминалка {reminder_template[user_id]['title']}."
                                           f" Не забудьте: {', '.join(items)}. Мне повторить?",
                                    'buttons': []
                                },
                                "session": session,
                                "version": version
                            }
                            answer_response = create_buttons(*[{"title": "Да", "hide": True},
                                                               {"title": "Нет", "hide": True}],
                                                             **answer_response)
                            states_dict[user_id].set_using()
                            return jsonify(answer_response)

                        answer_response = {
                            "response": {
                                'text': f"Такой напоминалки не существует",
                                'tts': f"Такой напоминалки не существует"
                            },
                            "session": session,
                            "version": version
                        }
                        return jsonify(answer_response)

                answer_response = {
                    "response": {
                        'text': f"Вы не назвали напоминалку, которую хотите использовать",
                        'tts': f"Вы не назвали напоминалку, которую хотите использовать"
                    },
                    "session": session,
                    "version": version
                }
                return jsonify(answer_response)

            if command == 'удалить':
                states_dict[user_id].set_delete()
                answer_response = {
                    "response": {
                        'text': 'Назовите название напоминалки, которую вы хотите удалить',
                        'tts': 'Назовите название напоминалки, которую вы хотите удалить'
                    },

                    "session": session,
                    "version": version
                }
                return jsonify(answer_response)

            if "удалить" in command:
                reminder_from_user = command.split()
                if len(reminder_from_user) != 1:
                    if 'напоминалк' in command:
                        index = str(command).find('напоминалк')
                        title = command[index + len('напоминалка'):].strip()
                        reminder_template[user_id]["title"] = title
                        states_dict[user_id].set_creating()
                        answer_response = {
                            "response": {
                                'text': f"Мне удалить напоминалку с названием {title}?",
                                'tts': f"Мне удалить напоминалку с названием {title}?",
                                'buttons': []
                            },
                            "session": session,
                            "version": version
                        }
                        answer_response = create_buttons(*[{"title": "Да", "hide": True},
                                                           {"title": "Нет", "hide": True}],
                                                         **answer_response)
                        states_dict[user_id].set_delete(10)
                        return jsonify(answer_response)

            answer_response = {
                "response": {
                    'text': get_phrase("ZERO", "zero")['text'],
                    'tts': get_phrase("ZERO", "zero")['tts'],
                    'buttons': []
                },
                "session": session,
                "version": version
            }
            answer_response = create_buttons(*[{"title": "Создать", "hide": True},
                                               {"title": "Использовать", "hide": True},
                                               {"title": "Удалить", "hide": True},
                                               {"title": "Стоп", "hide": False, }
                                               ], **answer_response)
            return jsonify(answer_response)

        # Сценарий создания
        if states_dict[user_id].is_creating(1):
            if check_line(command):
                answer_response = {
                    "response": {
                        'text': "Теперь перечислите всё, что вы бы не хотели забыть.",
                        'tts': "Теперь перечислите всё, что вы бы не хотели забыть.",
                    },
                    "session": session,
                    "version": version
                }
                states_dict[user_id].set_stage(2)
                return jsonify(answer_response)
            answer_response = {
                "response": {
                    'text': get_error_phrase()["text"],
                    'tts': get_error_phrase()["tts"],
                },
                "session": session,
                "version": version
            }
            return jsonify(answer_response)

        if states_dict[user_id].is_creating(2):
            if command:
                nouns = set([word for word in command.split() if morph.parse(word)[0].tag.POS == 'NOUN'])
                [reminder_template[user_id]["reminder_list"].append(morph.parse(word)[0].normal_form) for word in nouns]
                answer_response = {
                    "response": get_phrase(states_dict[user_id].get_state(), "first_stage_addition"),
                    "session": session,
                    "version": version
                }
                states_dict[user_id].set_stage(3)
                return jsonify(answer_response)

        if states_dict[user_id].is_creating(3):
            if cliche_word := words_in_string(ADDITION_WORDS, command):
                words = command[command.index(cliche_word) + len(cliche_word):]
                nouns = set([word for word in words.split() if morph.parse(word)[0].tag.POS == 'NOUN'])
                [reminder_template[user_id]["reminder_list"].append(morph.parse(word)[0].normal_form) for word in nouns]
                answer_response = {
                    "response": get_phrase(states_dict[user_id].get_state(), "first_stage_second_addition"),
                    "session": session,
                    "version": version
                }
                return jsonify(answer_response)
            if words_in_string(["все", "хватит", "всё"], command):
                states_dict[user_id].set_zero()
                database.add_reminder(user_id, reminder_template)
                reminder_template.pop(user_id)
                answer_response = {
                    "response": {
                        'text': "Отлично! Теперь вы можете использовать напоминалку когда захотите.",
                        'tts': "<speaker audio=\"dialogs-upload/1bdbfde6-622e-402a-a4ed-debcf92d6854/06852eea-ea27-4123-899f-ce346ef920dd.opus\">",
                        'buttons': []
                    },
                    "session": session,
                    "version": version
                }
                answer_response = create_buttons(*[{"title": "Создать", "hide": True},
                                                   {"title": "Использовать", "hide": True},
                                                   {"title": "Удалить", "hide": True},
                                                   {"title": "Стоп", "hide": False, }
                                                   ], **answer_response)
                return jsonify(answer_response)
            answer_response = {
                "response": {
                    'text': get_error_phrase()["text"],
                    'tts': get_error_phrase()["tts"],
                },
                "session": session,
                "version": version
            }
            return jsonify(answer_response)

        if states_dict[user_id].is_creating(10):
            if command:
                if database.does_reminder_exists(user_id, command):
                    answer_response = {
                        "response": {
                            "text": "У вас уже есть напоминалка с таким названием. Придумайте новое",
                            "tts": "У вас уже есть напоминалка с таким названием. Придумайте новое"
                        },
                        "session": session,
                        "version": version
                    }
                    return answer_response
                reminder_template[user_id]["title"] = command
                answer_response = {
                    "response": {
                        'text': get_phrase(states_dict[user_id].get_state(), "first_stage_alt")['text'].format(command),
                        'tts': get_phrase(states_dict[user_id].get_state(), "first_stage_alt")['tts'].format(command),
                        'buttons': []
                    },
                    "session": session,
                    "version": version
                }
                answer_response = create_buttons(*[{"title": "Да", "hide": True},
                                                   {"title": "Нет", "hide": True}],
                                                 **answer_response)
                states_dict[user_id].set_stage(11)
                return jsonify(answer_response)
            answer_response = {
                "response": {
                    'text': get_error_phrase()["text"],
                    'tts': get_error_phrase()["tts"],
                },
                "session": session,
                "version": version
            }
            return jsonify(answer_response)

        if states_dict[user_id].is_creating(11):
            if "да" in command or "хочу" in command:
                answer_response = {
                    "response": {
                        'text': "Теперь перечислите всё, что вы бы не хотели забыть.",
                        'tts': "Теперь перечислите всё, что вы бы не хотели забыть.",
                    },
                    "session": session,
                    "version": version
                }
                states_dict[user_id].set_stage(2)
                return jsonify(answer_response)
            else:
                answer_response = {
                    "response": {
                        "text": "Хорошо, повторите ввод",
                        "tts": "Поняла, повторите название"
                    },
                    "version": version,
                    "session": session
                }
                states_dict[user_id].set_stage(10)
                return jsonify(answer_response)

        # Сценарий удаления
        if states_dict[user_id].is_delete(1):
            if command in list(map(lambda n: n["title"], database.get_reminders_with_owner(user_id))):
                reminder_template[user_id]["title"] = command
                answer_response = {
                    "response": {
                        "text": f'Вы уверены что хотите удалить напоминалку {command}?',
                        "tts": f'Вы уверены что хотите удалить напоминалку {command}?',
                        'buttons': []
                    },
                    "session": session,
                    "version": version
                }
                answer_response = create_buttons(*[{"title": "Да", "hide": True},
                                                   {"title": "Нет", "hide": True}],
                                                 **answer_response)
                states_dict[user_id].set_stage(2)
                return jsonify(answer_response)

            answer_response = {
                "response": {
                    'text': get_error_phrase("not_found_error")["text"].format(command),
                    'tts': get_error_phrase("not_found_error")["tts"].format(command),
                },
                "session": session,
                "version": version
            }
            return jsonify(answer_response)

        if states_dict[user_id].is_delete(2):
            if check_line(command):
                answer_response = {
                    "response": {
                        "text": f'Напоминалка {reminder_template[user_id]["title"]} удалена',
                        "tts": f'Напоминалка {reminder_template[user_id]["title"]} удалена',
                        'buttons': []
                    },
                    "session": session,
                    "version": version
                }
                answer_response = create_buttons(*[{"title": "Создать", "hide": True},
                                                   {"title": "Использовать", "hide": True},
                                                   {"title": "Удалить", "hide": True},
                                                   {"title": "Стоп", "hide": False, }
                                                   ], **answer_response)

                database.delete_reminder(user_id, reminder_template[user_id]["title"])
                states_dict[user_id].set_zero()
                return jsonify(answer_response)

        if states_dict[user_id].is_delete(10):
            if "да" in command or "хочу" in command:
                answer_response = {
                    "response": {
                        "text": f'Напоминалка {reminder_template[user_id]["title"]} удалена',
                        "tts": f'Напоминалка {reminder_template[user_id]["title"]} удалена',
                        'buttons': []
                    },
                    "session": session,
                    "version": version
                }
                answer_response = create_buttons(*[{"title": "Создать", "hide": True},
                                                   {"title": "Использовать", "hide": True},
                                                   {"title": "Удалить", "hide": True},
                                                   {"title": "Стоп", "hide": False, }
                                                   ], **answer_response)

                database.delete_reminder(user_id, reminder_template[user_id]["title"])
                states_dict[user_id].set_zero()
                return jsonify(answer_response)
            if "нет" in command or "не хочу" in command:
                answer_response = {
                    "response": {
                        "text": f'Отмена удаления',
                        "tts": f'Отмена удаления',
                        'buttons': []
                    },
                    "session": session,
                    "version": version
                }
                answer_response = create_buttons(*[{"title": "Создать", "hide": True},
                                                   {"title": "Использовать", "hide": True},
                                                   {"title": "Удалить", "hide": True},
                                                   {"title": "Стоп", "hide": False, }
                                                   ], **answer_response)

                database.delete_reminder(user_id, reminder_template[user_id]["title"])
                states_dict[user_id].set_zero()
                return jsonify(answer_response)

            if not check_line(command):
                answer_response = {
                    "response": {
                        "text": get_phrase(states_dict[user_id].get_state(), "first_stage_disagree")["text"],
                        "tts": get_phrase(states_dict[user_id].get_state(), "first_stage_disagree")["tts"],
                        'buttons': []
                    },
                    "session": session,
                    "version": version
                }
                answer_response = create_buttons(*[{"title": "Создать", "hide": True},
                                                   {"title": "Использовать", "hide": True},
                                                   {"title": "Удалить", "hide": True},
                                                   {"title": "Стоп", "hide": False, }
                                                   ], **answer_response)
                states_dict[user_id].set_zero()
                return jsonify(answer_response)

            answer_response = {
                "response": {
                    get_error_phrase()
                },
                "session": session,
                "version": version
            }
            return jsonify(answer_response)

        # если пользователь решит повторить список айтемов, мб стоит сделать по-другому, не меняя стейж
        if states_dict[user_id].is_using(1):
            if "да" in command or "хочу" in command:
                items = reminder_template[user_id]['reminder_list']
                formatted_items = list(map(lambda word: morph.parse(word)[0].inflect({'accs'}).word, items))
                answer_response = {
                    "response": {
                        "text": get_phrase(states_dict[user_id].get_state(), "first_stage")["tts"].format(
                            ", ".join(formatted_items)),
                        "tts": get_phrase(states_dict[user_id].get_state(), "first_stage")["tts"].format(
                            ", ".join(formatted_items)),
                        'buttons': []
                    },
                    "session": session,
                    "version": version
                }
                answer_response = create_buttons(*[{"title": "Да", "hide": True},
                                                   {"title": "Нет", "hide": True}],
                                                 **answer_response)
                return jsonify(answer_response)
            answer_response = {
                "response": {
                    "text": get_phrase(states_dict[user_id].get_state(), "first_stage_disagree")["text"],
                    "tts": get_phrase(states_dict[user_id].get_state(), "first_stage_disagree")["tts"],
                    "buttons": [],
                },
                "session": session,
                "version": version
            }
            answer_response = create_buttons(*[{"title": "Создать", "hide": True},
                                               {"title": "Использовать", "hide": True},
                                               {"title": "Удалить", "hide": True},
                                               {"title": "Стоп", "hide": False, }
                                               ], **answer_response)
            states_dict[user_id].set_zero()
            return jsonify(answer_response)

        if states_dict[user_id].is_using(10):
            reminder_from_user = command.split()
            title = command.replace('использовать', '').replace('напоминалку', '').strip()
            try:
                items = database.get_reminder_items(user_id, title).split(";")
            except Exception:
                answer_response = {
                    "response": {
                        'text': f"Я не нашла такой напоминалки",
                        'tts': f"Я не нашла такой напоминалки",
                        "buttons": []
                    },
                    "session": session,
                    "version": version
                }
                answer_response = create_buttons(*[{"title": "Создать", "hide": True},
                                                   {"title": "Использовать", "hide": True},
                                                   {"title": "Удалить", "hide": True},
                                                   {"title": "Стоп", "hide": False, }
                                                   ], **answer_response)
                states_dict[user_id].set_zero()
                return jsonify(answer_response)
            reminder_template[user_id] = {}
            reminder_template[user_id]['title'] = title
            reminder_template[user_id]['reminder_list'] = items

            formatted_items = list(map(lambda word: morph.parse(word)[0].inflect({'accs'}).word, items))

            answer_response = {
                "response": {
                    'text': f"Напоминалка {reminder_from_user[0]}. Не забудьте {', '.join(formatted_items)}. Мне повторить?",
                    'tts': f"Напоминалка {reminder_from_user[0]}. Не забудьте {', '.join(formatted_items)}. Мне повторить?",
                    'buttons': []
                },
                "session": session,
                "version": version
            }
            answer_response = create_buttons(*[{"title": "Да", "hide": True},
                                               {"title": "Нет", "hide": True}],
                                             **answer_response)
            states_dict[user_id].set_using()
            return jsonify(answer_response)
        answer_response = {
            "response": {
                'text': f"Вы не назвали название напоминалки, которую хотите использовать",
                'tts': f"Вы не назвали название напоминалки, которую хотите использовать"
            },
            "session": session,
            "version": version
        }
        return jsonify(answer_response)


if __name__ == '__main__':
    app.run()
