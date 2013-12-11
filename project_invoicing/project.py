# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
#   project_invoicing for OpenERP                                             #
#   Copyright (C) 2012 Akretion Benoît GUILLOT <benoit.guillot@akretion.com>  #
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as            #
#   published by the Free Software Foundation, either version 3 of the        #
#   License, or (at your option) any later version.                           #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################

from openerp.osv import fields, orm
import time
from tools.translate import _
from openerp.osv.osv import except_osv
import openerp.addons.decimal_precision as dp


class project_task(orm.Model):
    _inherit = "project.task"

    _columns = {
        'product_id': fields.many2one('product.product', 'Product'),#use for pack

        'invoice_line_ids': fields.one2many('account.invoice.line', 'task_id',
                                            'Invoice Lines'),
        'fixed_amount': fields.boolean('Fixed Amount'),
        'price': fields.float('Price', digits_compute=dp.get_precision('Product Price')),
        'unit_price': fields.related('sale_order_line_id', 'price_unit',
                                     type='float', relation='sale.order.line',
                                     string="Unit Price"),
    }

    def _prepare_invoice_line_vals(self, cr, uid, task, context=None):
        fiscal_pos_obj = self.pool.get('account.fiscal.position')
        product = self._get_task_product(cr, uid, task, context=context)
        if not product:
            raise except_osv(_('Error'), _('At least one task has no product !'))
        general_account = product.product_tmpl_id.property_account_income or product.categ_id.property_account_income_categ
        taxes = product.taxes_id
        tax = fiscal_pos_obj.map_tax(cr, uid,
                                     task.project_id.partner_id.property_account_position,
                                     taxes)
        invoice_line_vals = {
                    'price_unit': task.planned_amount,
                    'quantity': 1,
                    'invoice_line_tax_id': [(6,0,tax )],
                    'name': task.name,
                    'product_id': product.id,
                    'invoice_line_tax_id': [(6,0,tax)],
                    'uos_id': product.uom_id.id,
                    'account_id': general_account.id,
                    'account_analytic_id': task.project_id.analytic_account_id.id,
                    'user_id': task.user_id.id,
                    'task_id': task.id,
        }
        return invoice_line_vals

    def _prepare_invoice_vals(self, cr, uid, project, grouped_tasks, context=None):
        account_payment_term_obj = self.pool.get('account.payment.term')
        partner = project.partner_id
        if (not partner) or not (project.pricelist_id):
            raise except_osv(_('Analytic Account incomplete'),
                        _('Please fill in the Partner or Customer and Sale '
                          'Pricelist fields in the Analytic Account:\n%s') % (project.name,))

        #Garder ou pas ?
        #date_due = False
        #if partner.property_payment_term:
        #    pterm_list= account_payment_term_obj.compute(cr, uid,
        #            partner.property_payment_term.id, value=1,
        #            date_ref=time.strftime('%Y-%m-%d'))
        #    if pterm_list:
        #        pterm_list = [line[0] for line in pterm_list]
        #        pterm_list.sort()
        #        date_due = pterm_list[-1]

        invoice_vals = {
            'name': time.strftime('%d/%m/%Y') + ' - ' + project.name,
            'partner_id': partner.id,
            'payment_term': partner.property_payment_term.id or False,
            'account_id': partner.property_account_receivable.id,
            'currency_id': project.pricelist_id.currency_id.id,
            #'date_due': date_due,
            'fiscal_position': partner.property_account_position.id
        }
        lines_vals = []
        for task in grouped_tasks:
            line_vals = self._prepare_invoice_line_vals(cr, uid, task, context=context)
            lines_vals.append([0, 0, line_vals])
        invoice_vals['invoice_line'] = lines_vals
        return invoice_vals

    def invoice_cost_create(self, cr, uid, ids, context=None):
        invoice_obj = self.pool.get('account.invoice')
        invoice_ids = []
        project_dict = {}
        for task in self.browse(cr, uid, ids, context=context):
            if not task.fixed_amount:
                raise except_osv(_('Error'),
                                 _('The task should not be invoiced that way'))
            if project_dict.get(task.project_id):
                project_dict[task.project_id].append(task)
            else:
                project_dict[task.project_id] = [task]
        for project, grouped_tasks in project_dict.items():
            invoice_vals =  self._prepare_invoice_vals(cr, uid,
                                                       project,
                                                       grouped_tasks,
                                                       context=context)
            invoice_id = invoice_obj.create(cr, uid, invoice_vals, context=context)
            invoice_ids.append(invoice_id)
            invoice_obj.button_reset_taxes(cr, uid, [invoice_id], context)
        return invoice_ids


class HrAnalyticTimesheet(orm.Model):
    _inherit = "hr.analytic.timesheet"

    _columns = {
        #MAYBE REPLACE BY SUBCONTRACTOR
        'invoice_line_id': fields.many2one('account.invoice.line', 'Invoice Line'),
    }

    def on_change_unit_amount(self, cr, uid, sheet_id, prod_id, unit_amount,
                              company_id, unit=False, journal_id=False,
                              task_id=False, to_invoice=False, context=None):
        res = super(HrAnalyticTimesheet, self).on_change_unit_amount(
            cr, uid, sheet_id, prod_id, unit_amount, company_id, unit,
            journal_id, task_id, to_invoice, context)
        if 'value' in res and task_id:
            task_obj = self.pool.get('project.task')
            task = task_obj.browse(cr, uid, task_id)
            if task.fixed_amount:
                res['value']['to_invoice'] = False
        return res

    def on_change_user_id(self, cr, uid, ids, user_id, parent_product_id):
        res = super(HrAnalyticTimesheet, self).on_change_user_id(cr, uid, ids, user_id)
        if parent_product_id:
            if not res.get('value'):
                res['value'] = {}
            res['value']['product_id'] = parent_product_id
        return res
