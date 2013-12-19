# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
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

import time
## Create an invoice based on selected timesheet lines
#

# TODO refactor all of this bullshit indeed it was based on the ugly wizard of OpenERP SA
# We should rewrite it totaly from scrath

from openerp.osv import fields, orm
from openerp.tools.translate import _
from collections import defaultdict
from openerp.osv.osv import except_osv

class hr_timesheet_project_invoice_create(orm.TransientModel):
    _name = 'hr.timesheet.project.invoice.create'
    _description = 'Create invoice from project timesheet'

    def view_init(self, cr, uid, fields, context=None):
        """
        This function checks for precondition before wizard executes
        @param self: The object pointer
        @param cr: the current row, from the database cursor,
        @param uid: the current user’s ID for security checks,
        @param fields: List of fields for default value
        @param context: A standard dictionary for contextual values
        """
        hr_analytic_obj = self.pool.get('hr.analytic.timesheet')
        hr_analytic_ids = context and context.get('active_ids', [])
        for hr_analytic in hr_analytic_obj.browse(cr, uid, hr_analytic_ids, context=context):
            if hr_analytic.invoice_id:
                raise osv.except_osv(_('Warning!'),
                    _("Invoice is already linked to the analytic line!") %hr_analytic.name)
            if not hr_analytic.to_invoice:
                raise osv.except_osv(_('Warning!'),
                    _("the analytic line %s can not be invoiced!")%hr_analytic.name)

    def do_create(self, cr, uid, ids, context=None):
        # Create an invoice based on selected timesheet lines
        timesheet_obj = self.pool.get('hr.analytic.timesheet')
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')

        data = self.read(cr, uid, ids, [], context=context)[0]
        inv_ids = timesheet_obj.create_invoice(cr, uid,
            context['active_ids'], data, context=context)
        mod_ids = mod_obj.search(cr, uid, [
            ('name', '=', 'action_invoice_tree1')
            ], context=context)[0]
        res_id = mod_obj.read(cr, uid, mod_ids, ['res_id'], context=context)['res_id']
        act_win = act_obj.read(cr, uid, res_id, [], context=context)
        act_win['domain'] = [('id', 'in', inv_ids),('type', '=', 'out_invoice')]
        act_win['name'] = _('Invoices')
        return act_win


