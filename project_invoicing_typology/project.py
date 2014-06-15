# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP
#   Copyright (C) 2012-TODAY Akretion (http://www.akretion.com).
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
#           Benoît GUILLOT <benoit.guillot@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp.osv import fields, orm


class project_typology(orm.Model):
    _inherit = 'project.typology'
    _columns = {
        'is_invoice_group_key': fields.boolean(
            'Grouping Key for Invoicing',
            help=('Tic that box if you want to group the task linked to this'
                  'typology base on the typology id instead of the task id')),
        'name': fields.char('Name', size=64, required=True, translate=True),
        'product_id': fields.many2one('product.product', 'Product'),
    }

class project_task(orm.Model):
    _inherit = "project.task"

    def _get_task_product(self, cr, uid, task, context=None):
        #TODO call super
        
        product = False
        if task.product_id:
            product = task.product_id
        elif task.typology_id:
            product = task.typology_id.product_id
        return product


class hr_analytic_timesheet(orm.Model):
    _inherit = "hr.analytic.timesheet"

    def _get_group_key(self, cr, uid, line, context=None):
        keys = super(hr_analytic_timesheet, self).\
            _get_group_key(cr, uid, line, context=context)
        if line.task_id.typology_id and \
           line.task_id.typology_id.is_invoicegroup_key:
            keys.append('task_id.typology_id.id')
            keys.remove('task_id.id')
        return keys

    def _prepare_invoice_line_vals(self, cr, uid, line, account, invoice,
                                   context=None):
        vals = super(hr_analytic_timesheet, self)._prepare_invoice_line_vals(
            cr, uid, line, account, invoice, context=context)
        if line.task_id.typology_id and \
           line.task_id.typology_id.is_invoice_group_key:
            vals['name'] = line.task_id.typology_id.name
        return res
