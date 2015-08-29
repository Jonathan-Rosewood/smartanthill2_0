# Copyright (C) 2015 OLogN Technologies AG
#
# This source file is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License version 2
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

from string import Template


class SourceGenerator(object):

    COPYRIGHT = """
/*******************************************************************************
Copyright (C) 2015 OLogN Technologies AG

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License version 2 as
    published by the Free Software Foundation.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
*******************************************************************************/

/*******************************************************************************
THIS FILE IS AUTOMATICALLY GENERATED BASED ON DESIRED PLUGIN LIST, SETTINGS
*******************************************************************************/
"""

    def get_content(self):
        raise NotImplementedError

    def generate(self):
        return "%s\n%s" % (self.COPYRIGHT.strip(), self.get_content())


class ZeptoConfigH(SourceGenerator):

    TPL = Template("""

#if !defined __ZEPTO_CONFIG_H__
#define __ZEPTO_CONFIG_H__

#define DECLARE_AES_ENCRYPTION_KEY \
const uint8_t AES_ENCRYPTION_KEY[16] ZEPTO_PROG_CONSTANT_LOCATION = \
{ ${AES_ENCRYPTION_KEY} }; \

#define DECLARE_DEVICE_ID \
uint16_t DEVICE_SELF_ID = 1;

#endif // __ZEPTO_CONFIG_H__
""")

    def __init__(self, config):
        self.config = config

    def get_content(self):
        return self.TPL.substitute(
            AES_ENCRYPTION_KEY=", ".join(
                [str(s) for s in self.config['AES_ENCRYPTION_KEY']])
        )


class BodyPartListCPP(SourceGenerator):

    TPL = Template("""
#include <simpleiot/siot_bodypart_list.h>

// include declarations of respective plugins
${plugin_includes}

${plugin_configs}

${plugin_states}

const uint8_t SA_BODYPARTS_MAX ZEPTO_PROG_CONSTANT_LOCATION = ${bodypart_nums};
const bodypart_item bodyparts[${bodypart_nums}] ZEPTO_PROG_CONSTANT_LOCATION =
{
    ${bodypart_items}
};
""")

    def __init__(self, bodyparts):
        self.bodyparts = bodyparts

    def get_content(self):
        return self.TPL.substitute(
            bodypart_nums=len(self.bodyparts),
            plugin_includes="\n".join(self._gen_plugin_includes()),
            plugin_configs="\n".join(self._gen_plugin_configs()),
            plugin_states="\n".join(self._gen_plugin_states()),
            bodypart_items=",\n".join(self._gen_bodypart_items()),
        )

    def _gen_plugin_includes(self):
        includes = set()
        for bodypart in self.bodyparts:
            includes.add('#include "plugins/{pid}/{pid}.h"'.format(
                pid=bodypart.plugin.get_id()))
        return list(includes)

    def _gen_plugin_configs(self):
        configs = []
        for bodypart in self.bodyparts:

            data = []
            for items in (bodypart.get_peripheral(), bodypart.get_options()):
                if not items:
                    continue
                for item in items:
                    if item['type'].startswith("char["):
                        data.append('.%s="%s"' % (item['name'], item['value']))
                    else:
                        data.append(".%s=%s" % (item['name'], item['value']))

            config = (
                "{pid}_plugin_config {pid}_plugin_config_{bpid}"
                .format(bpid=bodypart.get_id(),
                        pid=bodypart.plugin.get_id())
            )
            if data:
                config += "={ %s }" % ", ".join(data)
            configs.append(config + ";")

        return configs

    def _gen_plugin_states(self):
        states = []
        for bodypart in self.bodyparts:
            states.append(
                "{pid}_plugin_state {pid}_plugin_state_{bpid};\n"
                "{pid}_plugin_persistent_state "
                "{pid}_plugin_persistent_state_{bpid};"
                .format(pid=bodypart.plugin.get_id(), bpid=bodypart.get_id())
            )
        return states

    def _gen_bodypart_items(self):
        bpitems = []
        for bodypart in self.bodyparts:
            bpitems.append(
                "{{ {pid}_plugin_handler_init, {pid}_plugin_exec_init, "
                "{pid}_plugin_handler, &{pid}_plugin_config_{bpid}, "
                "&{pid}_plugin_persistent_state_{bpid}, NULL }}"
                .format(pid=bodypart.plugin.get_id(), bpid=bodypart.get_id())
            )
        return bpitems


class BusListCPP(SourceGenerator):

    TPL = Template("""
#include "sa_transports_list.h"
""")

    def __init__(self, buses):
        self.buses = buses

    def get_content(self):
        return self.TPL.substitute()
