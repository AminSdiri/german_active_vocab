import os
import re

from pathlib import Path

import anki
import click
from aqt.profiles import ProfileManager

from autologging import traced


@traced
class Anki:
    """My Anki collection wrapper class."""

    def __init__(self, base=None, path=None, profile=None, **_kwargs):
        self.modified = False

        self._init_load_collection(base, path, profile)

        self.model_name_to_id = {m['name']: m['id']
                                 for m in self.col.models.all()}
        self.model_names = self.model_name_to_id.keys()

        self.deck_name_to_id = {d['name']: d['id']
                                for d in self.col.decks.all()}
        self.deck_names = self.deck_name_to_id.keys()
        self.n_decks = len(self.deck_names)

    def _init_load_collection(self, base, path, profile):
        """Load the Anki collection"""
        # Save CWD (because Anki changes it)
        save_cwd = os.getcwd()

        if path is None:
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
        else:
            self.pm = None

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

    # @staticmethod
    # def _init_load_config():
    #     """Load custom configuration"""
    #     # Update LaTeX commands
    #     # * Idea based on Anki addon #1546037973 ("Edit LaTeX build process")
    #     if 'pngCommands' in cfg:
    #         anki.latex.pngCommands = cfg['pngCommands']
    #     if 'svgCommands' in cfg:
    #         anki.latex.svgCommands = cfg['svgCommands']

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

    def add_notes_single(self, fields, tags='', model=None, deck=None):
        """Add new note to collection"""
        if model is not None:
            self.set_model(model)

        notetype = self.col.models.current(for_deck=False)
        note = self.col.new_note(notetype)

        if deck is not None:
            note.note_type()['did'] = self.deck_name_to_id[deck]

        note.fields = [plain_to_html(x) for x in fields]

        tags = tags.strip().split()
        for tag in tags:
            note.add_tag(tag)

        if not note.dupeOrEmpty():
            self.col.addNote(note)
            self.modified = True
        else:
            click.secho('Dupe detected, note was not added!', fg='red')
            click.echo('Question:')
            click.echo(list(fields)[0])

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
    with Anki(**anki_cfg) as a:
        a.add_notes_single(['a8', 'b8'], tags='', model=None, deck=None)
    print('done')

