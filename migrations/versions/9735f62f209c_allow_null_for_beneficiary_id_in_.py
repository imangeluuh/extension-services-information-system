"""allow null for beneficiary id in response model for evaluation taken by assigned students

Revision ID: 9735f62f209c
Revises: 1f1cf69e79a1
Create Date: 2023-12-27 00:53:34.855074

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9735f62f209c'
down_revision = '1f1cf69e79a1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Response', schema=None) as batch_op:
        batch_op.alter_column('BeneficiaryId',
               existing_type=sa.VARCHAR(length=36),
               nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Response', schema=None) as batch_op:
        batch_op.alter_column('BeneficiaryId',
               existing_type=sa.VARCHAR(length=36),
               nullable=False)

    # ### end Alembic commands ###
