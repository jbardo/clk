#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function, absolute_import

import collections
from itertools import cycle

import click

from click_project.decorators import flag, option
from click_project.config import config
from click_project.lib import clear_ansi_color_codes
from click_project.core import ColorType


class Colorer(object):

    def __init__(self, kwargs):
        with_legend = kwargs.pop("with_legend")
        self.legend = kwargs.pop("legend")
        self.full = kwargs.pop("full")
        self.legend = self.legend or with_legend
        color = kwargs.pop("color")
        if color is False:
            self.legend = False
        self.kwargs = kwargs

        def compute_preset_colors(profile):
            """Return the same colors as the profile, swapping the underline parameter

            For example, if the profile is configured to have underline on, the underlined is off.
            """
            colors = kwargs[f"{profile}_color"].copy()
            colors["underline"] = not colors.get("underline")
            return colors

        self.profile_to_color = collections.defaultdict(dict)
        self.profile_to_color["global"] = kwargs["global_color"]
        self.profile_to_color["globalpreset"] = compute_preset_colors("global")
        if config.local_profile:
            self.profile_to_color["workgroup"] = kwargs.get("workgroup_color")
            self.profile_to_color["workgrouppreset"] = compute_preset_colors("workgroup")
            self.profile_to_color["local"] = kwargs.get("local_color")
            self.profile_to_color["localpreset"] = compute_preset_colors("local")
        for recipe in config.all_enabled_recipes:
            self.profile_to_color[recipe.name] = kwargs[
                recipe.name.replace("/", "_") + "_color"
            ]
        self.profile_to_color["env"] = {"bold": True}
        if not color:
            for key in self.profile_to_color.copy():
                self.profile_to_color[key] = None
        self.used_profiles = set()

    @property
    def profilenames_to_show(self):
        return [
            profile.name for profile in config.all_profiles
            if self.full or profile.explicit
        ]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.legend:
            colored_profiles = self.colorize_values(
                {
                    profile: (
                        profile
                        if "-" not in profile
                        else config.get_recipe(profile).friendly_name
                    )
                    for profile in self.profilenames_to_show
                }
            )
            message = "Legend: " + ", ".join(
                colored_profiles[profile]
                for profile in self.profilenames_to_show
                if profile in self.used_profiles
            )
            click.secho("-" * len(clear_ansi_color_codes(message)), dim=True)
            click.echo(message)

    def last_profile_of_settings(self, name, all_settings):
        for profile in reversed(self.profilenames_to_show):
            if profile in all_settings and name in all_settings[profile]:
                return profile

    @staticmethod
    def color_options(f):
        colors = cycle([
            "fg-yellow",
            "fg-blue",
            "bold-True,fg-yellow",
            "bold-True,fg-blue",
            "bold-True,fg-cyan",
            "bold-True,fg-green",
            "bold-True,fg-magenta",
            "fg-red",
            "bold-True,fg-red",
        ])
        f = flag("--with-legend/--without-legend", help="Start with a legend on colors",
                 deprecated="please use --legend instead")(f)
        f = flag("--legend/--no-legend",
                 default=config.get_value('config.color.legend') or False,
                 help="Start with a legend on colors")(f)
        f = flag('--color/--no-color', default=True, help="Show profiles in color")(f)
        f = flag('--full', help="Show the full information, even those guessed from the context")(f)
        shortname_color = {}

        for profile in config.all_profiles:
            if profile.default_color is None:
                if profile.short_name not in shortname_color:
                    shortname_color[profile.short_name] = next(colors)
                default_color = shortname_color[profile.short_name]
            else:
                default_color = profile.default_color
            f = option(f'--{profile.name.replace("/", "-")}-color',
                       help=f"Color to show the {profile.name} profile",
                       type=ColorType(), default=default_color)(f)
        return f

    def apply_color(self, string, profile):
        return click.style(string, **self.get_style(profile))

    def echo(self, message, profile):
        click.echo(self.apply_color(message, profile))

    def get_style(self, profile):
        self.used_profiles.add(profile)
        style = config.alt_style.copy()
        style.update(self.profile_to_color[profile] or {})
        return style

    def colorize_values(self, elems):
        return {
            profile:
            click.style(elem, **self.get_style(profile)) if elem else elem
            for profile, elem in elems.items()
        }

    def colorize(self, values, readprofile):
        args = []
        values = self.colorize_values(values)
        if readprofile == "context":
            args = self.combine(values)
        else:
            readprofiles = [readprofile] + [
                rl for rl in self.profilenames_to_show
                if rl.startswith(readprofile + "-")
            ]
            args = self.combine(
                {
                    rl: values[rl]
                    for rl in readprofiles
                })
        return args

    def combine(self, values):
        args = []
        for profile_name in self.profilenames_to_show:
            value = values.get(profile_name)
            if value:
                args.append(value)
        return args
