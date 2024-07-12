from health_check.views import MainView


class HealthCheckPingdomView(MainView):
    template_name = "pingdom.xml"

    def render_to_response(self, context, status):
        context["errored_plugins"] = [plugin for plugin in context["plugins"] if plugin.errors]
        print("********* errored_plugins: ", context["errored_plugins"])
        [print(plugin) for plugin in context["plugins"]]
        print("********* context: ", context)
        print("********* status: ", status)
        context["total_response_time"] = sum([plugin.time_taken for plugin in context["plugins"]])
        return super().render_to_response(context=context, status=status, content_type="text/xml")
