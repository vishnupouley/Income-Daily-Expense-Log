from django.db import models
from django.utils.translation import gettext as _

# Create your models here.

class MonthLog(models.Model):
    _id = models.AutoField(primary_key=True)
    time = models.DateTimeField(_("Time"),auto_now_add=True)
    description = models.TextField(_("Description"))
    amount = models.DecimalField(_("Amount"),max_digits=10, decimal_places=2)
    
    def __str__(self):
        return self.description

    def get_amount(self):
        return f"₹{self.amount}"

    class Meta:
        verbose_name = _("Month Log")
        verbose_name_plural = _("Month Logs")
        app_label = "month_log"


class MonthSalary(models.Model):
    _id = models.AutoField(primary_key=True)
    salary = models.DecimalField("_(Salary)",max_digits=10, decimal_places=2)
    date_of_salary = models.DateField("_(Date of Salary)")
    