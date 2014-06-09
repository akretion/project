# -*- coding: utf-8 -*-
###############################################################################
#
#   Module for OpenERP
#   Copyright (C) 2014 Akretion (http://www.akretion.com). All Rights Reserved
#   @author Benoît GUILLOT <benoit.guillot@akretion.com>
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


class project_issue_support_level(orm.Model):
    _name = "project.issue.level"
    _descritpion = "Support level linked to product and project issue"

    _columns = {
        'name': fields.char('Name', translate=True, size=64, required=True),
        'sequence': fields.integer('Sequence'),
        'product_id': fields.many2one(
            'product.product',
            'Product',
            required=True,
            help="Product linked to the support level for the pricing of the "
            "issue"),
        }


class project_issue(orm.Model):
    _inherit = "project.issue"

    _columns = {
        'support_level_id': fields.many2one(
            'project.issue.level',
            'Support level',
            required=True,
            readonly=True,
            states={'draft':[('readonly', False)]}),
        'product_id': fields.related(
            'support_level_id',
            'product_id',
            type='many2one',
            relation='product.product',
            string='Product',
            readonly=True),
    }

    def on_change_support_level(self, cr, uid, ids, support_level_id, context=None):
        level_obj = self.pool['project.issue.level']
        res = {}
        if support_level_id:
            product_id = level_obj.read(cr, uid, support_level_id,
                                        ['product_id'],
                                        context=context)['product_id'][0]
            res['value'] = {'product_id': product_id}
        return res

