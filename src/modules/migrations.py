import os
import sys
from typing import List, Optional

from yoyo import get_backend, read_migrations
from yoyo.migrations import MigrationList


class MigrationManager:
    def __init__(
        self,
        db_user: str,
        db_password: str,
        db_host: str,
        db_name: str,
        db_port: int,
        base_dir: str,
        migrations_dir: str = "migrations",
    ):
        self._base_dir: str = base_dir
        self.backend = get_backend(
            f"mysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        )
        self.migrations_path: str = os.path.join(base_dir, migrations_dir)

    def set_migrations_dir(self, migrations_dir: str):
        """
        Set migrations directory.
        :param migrations_dir: New migrations directory.
        :return:
        """
        self.migrations_path: str = os.path.join(self._base_dir, migrations_dir)

    @staticmethod
    def filter_migrations(
        migrations: MigrationList, migration_ids: List[str]
    ) -> MigrationList:
        """
        Filter migrations.
        :param migrations: List of fetched migrations.
        :param migration_ids: List of migration IDs to keep.
        :return: Filtered migration list.
        """
        return MigrationList(filter(lambda i: i.id in migration_ids, migrations))

    def apply(self, migration_ids: Optional[List[str]] = None):
        """
        Apply database migrations.
        """
        migrations = read_migrations(self.migrations_path)

        if migration_ids:
            migrations = self.filter_migrations(migrations, migration_ids)

        with self.backend.lock():
            self.backend.apply_migrations(self.backend.to_apply(migrations))

    def rollback(self, migration_ids: Optional[List[str]] = None):
        """
        Rollback database migrations.
        """
        migrations = read_migrations(self.migrations_path)

        if migration_ids:
            migrations = self.filter_migrations(migrations, migration_ids)

        with self.backend.lock():
            self.backend.rollback_migrations(self.backend.to_rollback(migrations))


def cli_execute():
    """
    Execute as CLI script.
    """
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.append(parent_dir)

    from const import ROOT_DIR, SETTINGS  # pylint: disable=R1722, C0415

    manager = MigrationManager(
        db_user=SETTINGS.db.user,
        db_password=SETTINGS.db.password,
        db_host=SETTINGS.db.host,
        db_port=SETTINGS.db.port,
        db_name=SETTINGS.db.name,
        base_dir=ROOT_DIR,
    )

    if len(sys.argv) == 1:
        print("Please provide a command, for example python migrations.py apply")
        sys.exit(1)

    func: Optional[callable] = getattr(manager, sys.argv[1], None)
    if func is None:
        print("Unknown command")
        sys.exit(1)

    if len(sys.argv) > 2:
        func(sys.argv[2:])
    else:
        func()

    print("Success!")


if __name__ == "__main__":
    cli_execute()
