# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP 
#   Copyright (C) 2013 Akretion (http://www.akretion.com).
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
#           Benoît GUILLOT <benoit.guillot@akretion.com>
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

from openerp.osv import orm, fields


class account_invoice_line(orm.Model):
    _inherit = "account.invoice.line"

    _columns = {
        'task_ids': fields.many2many('project.task', string='Task'),
        'timesheet_line_ids': fields.one2many(
            'hr.analytic.timesheet',
            'invoice_line_id',
            'Analytic Line'),
        'invoicing_type': fields.selection([
            ('fixed_amount', 'Fixed Amount'),
            ('time_base', 'Time Base'),
            ], 'Invoicing', required=True), 
    }

    _defaults = {
        'invoicing_type': 'time_base',
    }

