"""remove login table merge credentials to user table, remove child table for users

Revision ID: 6fb4005e6b9d
Revises: 0cde4519852f
Create Date: 2024-01-09 02:31:25.635865

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6fb4005e6b9d'
down_revision = '0cde4519852f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('Admin')
    op.drop_table('Student')
    with op.batch_alter_table('Login', schema=None) as batch_op:
        batch_op.drop_index('ix_Login_Email')

    op.drop_table('Login')
    op.drop_table('Faculty')
    with op.batch_alter_table('User', schema=None) as batch_op:
        batch_op.add_column(sa.Column('Email', sa.String(length=100), nullable=False))
        batch_op.add_column(sa.Column('Password', sa.String(length=60), nullable=False))
        batch_op.add_column(sa.Column('RoleId', sa.Integer(), nullable=False))
        batch_op.create_index(batch_op.f('ix_User_Email'), ['Email'], unique=True)
        batch_op.create_foreign_key(None, 'Role', ['RoleId'], ['RoleId'], ondelete='CASCADE')
        batch_op.drop_column('LoginId')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('User', schema=None) as batch_op:
        batch_op.add_column(sa.Column('LoginId', sa.VARCHAR(length=36), autoincrement=False, nullable=False))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.create_foreign_key('User_LoginId_fkey', 'Login', ['LoginId'], ['LoginId'], ondelete='CASCADE')
        batch_op.drop_index(batch_op.f('ix_User_Email'))
        batch_op.drop_column('RoleId')
        batch_op.drop_column('Password')
        batch_op.drop_column('Email')

    op.create_table('Faculty',
    sa.Column('FacultyId', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['FacultyId'], ['User.UserId'], name='Faculty_FacultyId_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('FacultyId', name='Faculty_pkey')
    )
    op.create_table('Login',
    sa.Column('LoginId', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.Column('Email', sa.VARCHAR(length=100), autoincrement=False, nullable=False),
    sa.Column('Password', sa.VARCHAR(length=60), autoincrement=False, nullable=False),
    sa.Column('Status', sa.VARCHAR(length=20), autoincrement=False, nullable=True),
    sa.Column('RoleId', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['RoleId'], ['Role.RoleId'], name='Login_RoleId_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('LoginId', name='Login_pkey'),
    postgresql_ignore_search_path=False
    )
    with op.batch_alter_table('Login', schema=None) as batch_op:
        batch_op.create_index('ix_Login_Email', ['Email'], unique=False)

    op.create_table('Student',
    sa.Column('SkillsInterest', sa.VARCHAR(length=255), autoincrement=False, nullable=False),
    sa.Column('StudentId', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['StudentId'], ['User.UserId'], name='Student_StudentId_fkey', ondelete='CASCADE')
    )
    op.create_table('Admin',
    sa.Column('AdminId', sa.VARCHAR(length=36), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['AdminId'], ['User.UserId'], name='Admin_AdminId_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('AdminId', name='Admin_pkey')
    )
    # ### end Alembic commands ###
