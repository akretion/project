# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015-TODAY Akretion (http://www.akretion.com)
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

from openerp import fields, api, models


class Project(models.Model):
    _inherit = 'project.project'

    issue_sequence_id = fields.Many2one('ir.sequence', string='Issue sequence',
                                        domain=[
                                            ('code', '=', 'project.task.issue')
                                        ])


class ProjectTask(models.Model):
    _inherit = 'project.task'

    issue_tracker_url = fields.Char('Bug tracker URL', size=255)
    issue_number = fields.Char('Issue number', size=64)
    display_name = fields.Char(string='Name',
                               compute='_compute_display_name')

    @api.multi
    def _read_group_stage_ids(self, domain, read_group_order=None, access_rights_uid=None):

        # TODO impmement access_right_uid
        stage_obj = self.env['project.task.type']
        order = stage_obj._order

        if read_group_order == 'stage_id desc':
            order = '%s desc' % order

        search_domain = []
        project_id = self._resolve_project_id_from_context()
        if project_id:
            search_domain.extend([('project_ids', '=', project_id)])

        stages = stage_obj.search(search_domain, order=order)

        fold = {}
        result = []
        for stage in stages:
            fold[stage.id] = stage.fold or False
            result.append((stage.id, stage.name))

        return result, fold

    _group_by_full = {
        'stage_id': _read_group_stage_ids,
    }

    @api.multi
    def _set_issue_number(self):
        sequence_obj = self.env['ir.sequence']
        for task in self:

            if not task.project_id:
                continue

            sequence = task.project_id.issue_sequence_id
            project_issue = self.env.ref('project_ak.project_issue')
            if task.project_id == project_issue and \
                    not task.issue_number and sequence:
                task.issue_number = sequence_obj.next_by_id(
                    sequence.id
                )

    @api.model
    def create(self, vals):
        task = super(ProjectTask, self).create(vals)
        task._set_issue_number()
        return task

    @api.multi
    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        self._set_issue_number()
        return res

    @api.one
    @api.depends('name', 'issue_number')
    def _compute_display_name(self):
        if self.issue_number:
            names = [self.issue_number, self.name]
            self.display_name = ' '.join(names)
        else:
            self.display_name = self.name
