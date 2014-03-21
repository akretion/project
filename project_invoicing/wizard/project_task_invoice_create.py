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

from tools.translate import _
from openerp.osv import orm


class project_task_invoice_create(orm.TransientModel):
    _name = 'project.task.invoice.create'

    _description = "Create invoice from project task"

    def view_init(self, cr, uid, fields, context=None):
        """
        This function checks for precondition before wizard executes
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param fields: List of fields for default value
        @param context: A standard dictionary for contextual values
        """
        task_obj = self.pool.get('project.task')
        task_ids = context and context.get('active_ids', [])
        for task in task_obj.browse(cr, uid, task_ids, context=context):
            if task.invoice_line_ids:
                raise orm.except_orm(
                    _('Warning!'),
                    _("Invoice lines are already linked to the task!"))
            if task.state != 'done':
                raise orm.except_orm(
                    _('Warning!'),
                    _("The task must be done is you want to invoice it!"))
            if not task.invoice_type != 'fixed_amount':
                raise orm.except_orm(
                    _('Warning!'),
                    _("This task has not a fixed amout, you should not invoice"
                      "it this way, use the wizard on the task work instead!"))

    def do_create(self, cr, uid, ids, context=None):
        invoice_ids = self.pool.get('project.task').create_invoice(
            cr, uid, context['active_ids'], context=context)
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        mod_ids = mod_obj.search(cr, uid, [
            ('name', '=', 'action_invoice_tree1')
            ], context=context)[0]
        res_id = mod_obj.read(cr, uid, mod_ids, ['res_id'], context=context)['res_id']
        act_win = act_obj.read(cr, uid, res_id, [], context=context)
        act_win['domain'] = [('id', 'in', invoice_ids), ('type', '=', 'out_invoice')]
        act_win['name'] = _('Invoices')
        return act_win
