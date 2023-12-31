"""change description data type from string(255) to text in activity model

Revision ID: 0605d4a58378
Revises: 9735f62f209c
Create Date: 2023-12-30 17:58:29.546741

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0605d4a58378'
down_revision = '9735f62f209c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Activity', schema=None) as batch_op:
        batch_op.alter_column('Description',
               existing_type=sa.VARCHAR(length=255),
               type_=sa.Text(),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Activity', schema=None) as batch_op:
        batch_op.alter_column('Description',
               existing_type=sa.Text(),
               type_=sa.VARCHAR(length=255),
               existing_nullable=False)

    # ### end Alembic commands ###
