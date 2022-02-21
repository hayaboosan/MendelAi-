"""empty message

Revision ID: d4e89e230efc
Revises: c147adcfd1b4
Create Date: 2022-02-22 06:48:55.726795

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd4e89e230efc'
down_revision = 'c147adcfd1b4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('farms', sa.Column('abbreviation', sa.String(length=50), nullable=True))
    op.create_unique_constraint(None, 'farms', ['abbreviation'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'farms', type_='unique')
    op.drop_column('farms', 'abbreviation')
    # ### end Alembic commands ###
