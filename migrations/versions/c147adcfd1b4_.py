"""empty message

Revision ID: c147adcfd1b4
Revises: 1d38678e9a6d
Create Date: 2022-02-22 06:48:03.123370

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c147adcfd1b4'
down_revision = '1d38678e9a6d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ai_stations', sa.Column('abbreviation', sa.String(length=50), nullable=True))
    op.create_unique_constraint(None, 'ai_stations', ['abbreviation'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'ai_stations', type_='unique')
    op.drop_column('ai_stations', 'abbreviation')
    # ### end Alembic commands ###