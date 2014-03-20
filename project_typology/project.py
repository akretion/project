# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 Akretion LDTA (<http://www.akretion.com>).
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm


class project_typology(orm.Model):
    _name = 'project.typology'
    _description = 'Type of tasks to organize projects'

    _columns = {
        'name': fields.char('Name', size=64, required=True, translate=True),
        'product_id': fields.many2one('product.product', 'Product'),
    }


class project_task(orm.Model):
    _inherit = 'project.task'

    _columns = {
        'typology_id': fields.many2one('project.typology', 'Typology'),
    }
