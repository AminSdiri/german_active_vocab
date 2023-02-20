import os
import re
import sys
import click
from pathlib import Path
from plyer import notification
import anki
sys.modules['PyQt6'] = None # prevent aqt from using PyQt6 to avoid names conflict if anki-qt6 app is installed
from aqt.profiles import ProfileManager

# TODO (2) baddel el echos lkol lenna des notifications w logger
# https://addon-docs.ankiweb.net/the-anki-module.html

class Anki:
    """My Anki collection wrapper class."""

    def __init__(self, base=None, profile=None):
        self.modified = False

        self._init_load_collection(base, profile)

        # DONE badel el model fih word w cloze w hint
        self.model_name_to_id = {m['name']: m['id']
                                 for m in self.col.models.all()}
        self.model_names = self.model_name_to_id.keys()

        self.deck_name_to_id = {d['name']: d['id']
                                for d in self.col.decks.all()}
        self.deck_names = self.deck_name_to_id.keys()
        self.n_decks = len(self.deck_names)

    def _init_load_collection(self, base, profile) -> None:
        """Load the Anki collection"""
        # Save CWD (because Anki changes it)
        save_cwd = os.getcwd()

        if base is None:
            click.echo('Base path is not properly set!')
            raise click.Abort()

        basepath = Path(base)
        if not (basepath / 'prefs21.db').exists():
            click.echo('Invalid base path!')
            click.echo(f'path = {basepath.absolute()}')
            raise click.Abort()

        # Initialize a profile manager to get an interface to the profile
        # settings and main database path; also required for syncing
        self.pm = ProfileManager(base)
        self.pm.setupMeta()

        if profile is None:
            profile = self.pm.profiles()[0]

        # Load the main Anki database/collection
        self.pm.load(profile)
        path = self.pm.collectionPath()

        try:
            self.col = anki.Collection(path)
        except AssertionError as error:
            click.echo('Path to database is not valid!')
            click.echo(f'path = {path}')
            raise click.Abort() from error
        except anki.errors.DBError as error:
            click.echo('Database is NA/locked!')
            notification.notify(title='Database is locked!',
                        message=f'Anki already open, or media currently syncing. please close Anki and try again".',
                        timeout=10)
            raise click.Abort() from error

        # Restore CWD (because Anki changes it)
        os.chdir(save_cwd)

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self.modified:
            click.echo('Database was modified.')
            if self.pm is not None and self.pm.profile['syncKey']:
                click.secho('Remember to sync!', fg='blue')
            self.col.close()
        elif self.col.db:
            self.col.close(False)
    
    def get_model(self, model_name):
        """Get model from model name"""
        return self.col.models.get(self.model_name_to_id.get(model_name))

    def set_model(self, model_name):
        """Set current model based on model name"""
        current = self.col.models.current(for_deck=False)
        if current['name'] == model_name:
            return current

        model = self.get_model(model_name)
        if model is None:
            click.secho(f'Model "{model_name}" was not recognized!')
            raise click.Abort()

        self.col.models.set_current(model)
        return model

    def add_anki_note(self, note_content, tags='', model=None, deck=None, overwrite_notes=False):
        """Add new note to collection"""
        if model is not None:
            self.set_model(model)

        notetype = self.col.models.current(for_deck=False)
        note = self.col.new_note(notetype)

        if deck is not None:
            note.note_type()['did'] = self.deck_name_to_id[deck]

        fields = [
            note_content['cloze'],
            note_content['hint1'],
            note_content['hint2'],
            note_content['hint3'],
            note_content['answer_extra']
            ]
        note.fields = [plain_to_html(x) for x in fields]

        tags = tags.strip().split()
        for tag in tags:
            note.add_tag(tag)

        note_id = None
        # NORMAL: NoteFieldsCheckResponse.State.ValueType  # 0
        # EMPTY: NoteFieldsCheckResponse.State.ValueType  # 1
        # DUPLICATE: NoteFieldsCheckResponse.State.ValueType  # 2
        # MISSING_CLOZE: NoteFieldsCheckResponse.State.ValueType  # 3
        # NOTETYPE_NOT_CLOZE: NoteFieldsCheckResponse.State.ValueType  # 4
        # FIELD_NOT_CLOZE: NoteFieldsCheckResponse.State.ValueType  # 5
        if not note.dupeOrEmpty():
            self.col.addNote(note)
            notification.notify(title='Anki: Note added.',
                        message=f'Front: "{list(fields)[0]}".',
                        timeout=10)
            note_id = note.id
            self.modified = True
        elif note.dupeOrEmpty() ==1:
            click.secho('Empty, note was not added!', fg='red')
            click.echo('Question:')
            click.echo(list(fields)[0])
            notification.notify(title='Anki: Empty Note.',
                        message=f'Front "{list(fields)[0]}" is empty. note was not added!',
                        timeout=10)
        elif note.dupeOrEmpty() ==2:
            # for notes that are already in anki but doesn't have an anki-note-id, 
            # that's why we're here and we have to fix that
            note_front = note.fields[0].replace('"', r'\"') # if it contains double quotes
            note_ids = self.col.find_notes(f'Text:"{note_front}"')
            print(1)
            assert len(note_ids) == 1, f'no notes or more than one note found with Text:"{note.fields[0]}"'
            note.id = note_ids[0]
            self.col.update_note(note)
            self.modified = True
            note_id = note.id
            notification.notify(title='Anki: Note updated.',
                    message=f'Front: "{list(fields)[0]}".',
                    timeout=10)
            click.secho('Dupe detected, got note id, note and word_dict got updated!', fg='red')
            click.echo('Question:')
            click.echo(list(fields)[0])
            notification.notify(title='Anki Dupe detected and updated.',
                        message=f'Front {list(fields)[0]} already exist. we got note id, note and word_dict got updated.',
                        timeout=10)
        else:
            click.secho('Invalid Note, note was not added!', fg='red')
            click.echo('Question:')
            click.echo(list(fields)[0])
            notification.notify(title='Anki: Invalid Note.',
                        message=f'Front {list(fields)[0]} is invalid. note was not added!',
                        timeout=10)
        return note_id
    
    def update_anki_note(self, note_content: dict, note_id: int, tags='', model=None):
        # DONE (1) add ability to only change note contents without changing review time and meta-informations
        # DONE (0)* add card ID to word_dict to be able to replace it after a change without resetting review data
        """update an already existing note"""
        if model is not None:
            self.set_model(model)

        note = self.col.get_note(note_id)

        fields = [
            note_content['cloze'],
            note_content['hint1'],
            note_content['hint2'],
            note_content['hint3'],
            note_content['answer_extra']
            ]
        note.fields = [plain_to_html(x) for x in fields]

        tags = tags.strip().split()
        for tag in tags:
            note.add_tag(tag)

        if not note.dupeOrEmpty():
            self.col.update_note(note)
            notification.notify(title='Anki: Note Updated.',
                        message=f'Front: "{list(fields)[0]}".',
                        timeout=10)
            note_id = note.id
            self.modified = True
        elif note.dupeOrEmpty() ==1:
            click.secho('Empty, note was not added!', fg='red')
            click.echo('Question:')
            click.echo(list(fields)[0])
            notification.notify(title='Anki: Empty Note.',
                        message=f'Front "{list(fields)[0]}" is empty. note was not added!',
                        timeout=10)
        elif note.dupeOrEmpty() ==2:
            notification.notify(title='Anki Dupe detected.',
                        message=f'Front {list(fields)[0]} already exist. note was updated!',
                        timeout=10)
            raise RuntimeError("note dupe detected though we're trying to update it")
        else:
            click.secho('Invalid Note, note was not added!', fg='red')
            click.echo('Question:')
            click.echo(list(fields)[0])
            notification.notify(title='Anki: Invalid Note.',
                        message=f'Front {list(fields)[0]} is invalid. note was not added!',
                        timeout=10)


    def sync(self):
        """Sync collection to AnkiWeb"""
        if self.pm is None:
            return

        auth = self.pm.sync_auth()
        if auth is None:
            return

        # Make sure database is saved first
        self.col.save(trx=False)

        # Perform main sync
        try:
            debug_output = 'anki::sync=debug' in os.environ.get('RUST_LOG', '')

            if debug_output:
                click.secho('Syncing deck:', fg='blue')
            else:
                click.echo('Syncing deck ... ', nl=False)

            self.col.sync_collection(auth)

            if not debug_output:
                click.echo('done!')
            else:
                click.echo('')
        except Exception as e:
            click.secho('Error during sync!', fg='red')
            click.echo(e)
            raise click.Abort()

        # Perform media sync
        try:
            debug_output = 'media=debug' in os.environ.get('RUST_LOG', '')

            with cd(self.col.media.dir()):
                if debug_output:
                    click.secho('Syncing media:', fg='blue')
                else:
                    click.echo('Syncing media ... ', nl=False)
                self.col.sync_media(auth)
                if not debug_output:
                    click.echo('done!')
        except Exception as e:
            if "sync cancelled" in str(e):
                return
            raise


class cd:
    """Context manager for changing the current working directory"""

    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)
        self.savedPath = None

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


def plain_to_html(plain):
    """Convert plain text to html"""
    # Minor clean up
    plain = plain.replace(r'&lt;', '<')
    plain = plain.replace(r'&gt;', '>')
    plain = plain.replace(r'&amp;', '&')
    plain = plain.replace(r'&nbsp;', ' ')
    plain = re.sub(r'\<b\>\s*\<\/b\>', '', plain)
    plain = re.sub(r'\<i\>\s*\<\/i\>', '', plain)
    plain = re.sub(r'\<div\>\s*\<\/div\>', '', plain)

    # Convert newlines to <br> tags
    plain = plain.replace('\n', '<br />')

    return plain.strip()


if __name__ == "__main__":
    # for testing
    # from settings import ANKI_CONFIG
    # with Anki(**ANKI_CONFIG) as a:
    #     a.add_notes_single(['a8', 'b8'], tags='', model=None, deck=None)
    print('done')
