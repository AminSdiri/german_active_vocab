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

    def add_notes_single(self, cloze, hint1='', hint2='', hint3='', answer_extra='', tags='', model=None, deck=None, overwrite_notes=False):
        # TODO (1)* add card ID to word_dict to be able to replace it after a change without resetting review data
        """Add new note to collection"""
        if model is not None:
            self.set_model(model)

        notetype = self.col.models.current(for_deck=False)
        note = self.col.new_note(notetype)

        if deck is not None:
            note.note_type()['did'] = self.deck_name_to_id[deck]

        fields = [cloze, hint1, hint2, hint3, answer_extra]
        note.fields = [plain_to_html(x) for x in fields]

        tags = tags.strip().split()
        for tag in tags:
            note.add_tag(tag)

        if not note.dupeOrEmpty():
            self.col.addNote(note)
            notification.notify(title='Anki: Note added.',
                        message=f'Front: "{list(fields)[0]}".',
                        timeout=10)
            self.modified = True
        elif note.dupeOrEmpty() ==1:
            click.secho('Empty, note was not added!', fg='red')
            click.echo('Question:')
            click.echo(list(fields)[0])
            notification.notify(title='Anki: Empty Note.',
                        message=f'Front "{list(fields)[0]}" is empty. note was not added!',
                        timeout=10)
        elif note.dupeOrEmpty() ==2:
            if overwrite_notes:
                # TODO (1) add ability to only change note contents without changing review time and meta-informations
                self.col.addNote(note)
                self.modified = True
            else:
                click.secho('Dupe detected, note was not added!', fg='red')
                click.echo('Question:')
                click.echo(list(fields)[0])
                notification.notify(title='Anki Dupe detected.',
                            message=f'Front {list(fields)[0]} already exist. note was not added!',
                            timeout=10)
        else:
            click.secho('Invalid Note, note was not added!', fg='red')
            click.echo('Question:')
            click.echo(list(fields)[0])
            notification.notify(title='Anki: Invalid Note.',
                        message=f'Front {list(fields)[0]} is invalid. note was not added!',
                        timeout=10)

        return note.dupeOrEmpty()


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
    from settings import ANKI_CONFIG
    with Anki(**ANKI_CONFIG) as a:
        a.add_notes_single(['a8', 'b8'], tags='', model=None, deck=None)
    print('done')
