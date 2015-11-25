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

    @api.multi
    def _set_issue_number(self):
        sequence_obj = self.env['ir.sequence']
        for task in self:

            if not task.project_id:
                continue

            sequence = task.project_id.issue_sequence_id
            project_issue = self.env.ref('project_task_issue.project_issue')
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
