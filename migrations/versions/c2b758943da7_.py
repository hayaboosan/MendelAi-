"""empty message

Revision ID: c2b758943da7
Revises: 67b37213b916
Create Date: 2022-02-21 05:05:36.330495

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2b758943da7'
down_revision = '67b37213b916'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        'farms', sa.Column('ai_station_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        None, 'farms', 'ai_stations', ['ai_station_id'], ['id'])

    op.add_column(
        'users', sa.Column('ai_station_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        None, 'users', 'ai_stations', ['ai_station_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_column('users', 'ai_station_id')

    op.drop_constraint(None, 'farms', type_='foreignkey')
    op.drop_column('farms', 'ai_station_id')
    # ### end Alembic commands ###
