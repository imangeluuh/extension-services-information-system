"""Change creator parent in announcement model

Revision ID: fd3a22b8b13b
Revises: 36654b554930
Create Date: 2023-10-26 22:31:08.862343

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd3a22b8b13b'
down_revision = '36654b554930'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Announcement', schema=None) as batch_op:
        batch_op.drop_constraint('Announcement_CreatorId_fkey', type_='foreignkey')
        batch_op.create_foreign_key(None, 'User', ['CreatorId'], ['UserId'], ondelete='CASCADE')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Announcement', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('Announcement_CreatorId_fkey', 'Admin', ['CreatorId'], ['AdminId'], ondelete='CASCADE')

    # ### end Alembic commands ###