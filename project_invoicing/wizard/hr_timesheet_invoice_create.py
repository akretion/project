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

from openerp.osv import fields, osv
from openerp.tools.translate import _
from collections import defaultdict
from openerp.osv.osv import except_osv

class hr_timesheet_project_invoice_create(osv.osv_memory):
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
                raise osv.except_osv(_('Warning!'), _("Invoice is already linked to the analytic line!") %hr_analytic.name)
            if not hr_analytic.to_invoice:
                raise osv.except_osv(_('Warning!'), _("the analytic line %s can not be invoiced!")%hr_analytic.name)

    def do_create(self, cr, uid, ids, context=None):
        data = self.read(cr, uid, ids, [], context=context)[0]
        # Create an invoice based on selected timesheet lines
        invs = self.pool.get('hr.analytic.timesheet').invoice_cost_create(cr, uid, context['active_ids'], data, context=context)
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        mod_ids = mod_obj.search(cr, uid, [('name', '=', 'action_invoice_tree1')], context=context)[0]
        res_id = mod_obj.read(cr, uid, mod_ids, ['res_id'], context=context)['res_id']
        act_win = act_obj.read(cr, uid, res_id, [], context=context)
        act_win['domain'] = [('id','in',invs),('type','=','out_invoice')]
        act_win['name'] = _('Invoices')
        return act_win

class hr_analytic_timesheet(osv.osv):
    _inherit = "hr.analytic.timesheet"

    def _get_group_key(self, cr, uid, context=None):
        return ['product_id', 'product_uom_id', 'user_id', 'task_id', 'issue_id']

    def _build_key(self, cr, uid, line, context=None):
        result = ''
        for key in self._get_group_key(cr, uid, context=context):
            result += "%s:%s|"%(key, line[key].id)
        return result

    def _check_line(self, cr, uid, line, context=None):
        if not line.account_id.partner_id:
            raise osv.except_osv(_('Hr Analytic Account incomplete !'),
                _('Please fill in the Partner on the Account:\n%s.') % (line.account_id.name,))
        if not line.account_id.pricelist_id: #still needed?
            raise osv.except_osv(_('Hr Analytic Account incomplete !'),
                _('Please fill in the Pricelist on the Account:\n%s.') % (line.account_id.name,))
        return True

    def group_lines(self, cr, uid, ids, context=None):
        """ return the line group"""
        result = defaultdict(lambda : defaultdict(list))
        for line in self.browse(cr, uid, ids, context=context):
            self._check_line(cr, uid, line, context=context)
            key = self._build_key(cr, uid, line, context=context)
            result[line.account_id][key].append(line)
        return result

    def _get_price(self, cr, uid, line, context=None):
        if line.task_id.unit_price:
            return line.task_id.unit_price
        elif line.product_id:
            pricelist = line.task_id.project_id.pricelist_id
            partner_id = line.task_id.project_id.partner_id.id
            price = pricelist.price_get(
                        line.product_id.id,
                        line.unit_amount or 1.0,
                        partner_id,
                        context=context)[pricelist.id]
            return price
        raise osv_except(_('USER ERROR'), _('NO PRICE HAVE BEEN FOUND'))


    def _play_onchange_on_line(self, cr, uid, line, invoice_vals, context=None):
        res = self.pool.get('account.invoice.line').product_id_change(cr, uid,
                    None,
                    line.product_id.id,
                    line.product_uom_id.id, 
                    qty = - line.amount,
                    type = 'out_invoice',
                    partner_id = invoice_vals['partner_id'],
                    fposition_id = invoice_vals['fiscal_position'],
                    currency_id = invoice_vals['currency_id'],
                    context = context,
                    company_id = invoice_vals['company_id'])
        return res.get('value', [])

    def _prepare_invoice_line_vals(self, cr, uid, line, account, invoice_vals, context=None):
        invoice_line = self._play_onchange_on_line(cr, uid, line, invoice_vals, context=context)
        invoice_line.update({
                'price_unit': self._get_price(cr, uid, line, context=context),
                'quantity': line.unit_amount,
                'discount':False,#TODO
                'name': line.task_id.name or line.issue_id.name,
                'product_id': line.product_id.id,
                'uos_id': line.product_uom_id.id,
                'account_analytic_id': account.id,
                'user_id': line.user_id.id,
                'task_id': line.task_id.id,
            })
        return invoice_line
    
    def _update_invoice_line_vals(self, cr, uid, line, invoice_line_vals, context=None):
        invoice_line_vals['quantity'] = invoice_line_vals['quantity'] - line.amount
        return invoice_line_vals

    def _prepare_invoice_vals(self, cr, uid, account, context=None):
        account_payment_term_obj = self.pool.get('account.payment.term')
        partner = account.partner_id
        date_due = False
        if partner.property_payment_term:
            pterm_list= account_payment_term_obj.compute(cr, uid,
                    partner.property_payment_term.id, value=1,
                    date_ref=time.strftime('%Y-%m-%d'))
            if pterm_list:
                pterm_list = [line[0] for line in pterm_list]
                pterm_list.sort()
                date_due = pterm_list[-1]

        return {
            'partner_id': account.partner_id.id,
            'company_id': account.company_id.id,
            'payment_term': partner.property_payment_term.id or False,
            'account_id': partner.property_account_receivable.id,
            'currency_id': account.pricelist_id.currency_id.id,
            'date_due': date_due,
            'fiscal_position': account.partner_id.property_account_position.id,
            'invoice_line': [],
        }

    def invoice_cost_create(self, cr, uid, ids, data=None, context=None):
        res_partner_obj = self.pool.get('res.partner')
        invoice_line_obj = self.pool.get('account.invoice.line')
        invoice_obj = self.pool.get('account.invoice')
        if context is None:
            context = {}
        invoices_ids=[]
        for account, group_lines in self.group_lines(cr, uid, ids, context=context).iteritems():
            invoice_vals = self._prepare_invoice_vals(cr, uid, account, context=context)
            ctx = context.copy()
            partner = res_partner_obj.browse(cr, uid, invoice_vals['partner_id'], context)
            ctx['lang'] = partner.lang
            # set company_id in context, so the correct default journal will be selected
            ctx['force_company'] = invoice_vals['company_id']
            # set force_company in context so the correct product properties are selected (eg. income account)
            ctx['company_id'] = invoice_vals['company_id']
            invoice_id = invoice_obj.create(cr, uid, invoice_vals, context=ctx)
            invoices_ids.append(invoice_id)
            for key in group_lines:
                line = group_lines[key].pop()
                invoice_line_vals = self._prepare_invoice_line_vals(cr, uid, line, account, invoice_vals, context=context)
                for line in group_lines[key]:
                    invoice_line_vals = self._update_invoice_line_vals(cr, uid, line, invoice_line_vals, context=context)
                invoice_line_vals['invoice_id'] = invoice_id
                inv_line_id = invoice_line_obj.create(cr, uid, invoice_line_vals, context=context)
                line.write({'invoice_line_id': inv_line_id}, context=context)
        return invoices_ids


