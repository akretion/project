# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP 
#   Copyright (C) 2013 Akretion (http://www.akretion.com).
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
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
from openerp.tools.translate import _


class HrEmployee(orm.Model):
    _inherit='hr.employee'

    def _get_employee(self, cr, uid, user_id, company_id, context=None):
        employee_id = self.search(cr, uid, [
            ['user_id', '=', user_id],
            ['company_id', '=', company_id],
            ], context=context)
        if not employee_id:
            raise orm.except_orm(
                _('Error'),
                _('No employee found for user_id %s and company_id %s'))
        elif len(employee_id) != 1:
            raise orm.except_orm(
                _('Error'),
                _('Too many employee found for user_id %s and company_id %s'))
        return self.browse(cr, uid, employee_id[0], context=context) 
