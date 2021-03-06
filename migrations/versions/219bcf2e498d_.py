"""empty message

Revision ID: 219bcf2e498d
Revises: a29dda0f5deb
Create Date: 2020-07-20 00:27:33.582257

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '219bcf2e498d'
down_revision = 'a29dda0f5deb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Shows', sa.Column('id', sa.Integer(), nullable=True))
    op.alter_column('Shows', 'artist_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.alter_column('Shows', 'venue_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('Shows', 'venue_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.alter_column('Shows', 'artist_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    op.drop_column('Shows', 'id')
    # ### end Alembic commands ###
