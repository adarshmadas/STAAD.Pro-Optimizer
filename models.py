from django.db import models


class UploadSession(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_name = models.CharField(max_length=255)
    total_members = models.IntegerField(default=0)

    def __str__(self):
        return f"Session {self.id} - {self.file_name}"


class MemberResult(models.Model):
    MEMBER_TYPES = [
        ('beam', 'Beam'),
        ('column', 'Column'),
        ('brace', 'Brace'),
    ]

    session = models.ForeignKey(UploadSession, on_delete=models.CASCADE, related_name='members')

    # Inputs
    member_id = models.CharField(max_length=50)
    member_type = models.CharField(max_length=50)
    span_m = models.FloatField()
    stories = models.IntegerField(default=1)
    axial_kN = models.FloatField()
    moment_x_kNm = models.FloatField()
    moment_z_kNm = models.FloatField()
    shear_y_kN = models.FloatField()
    deflection_mm = models.FloatField(default=0)
    utilization = models.FloatField()
    section_name = models.CharField(max_length=100, blank=True)
    current_area_cm2 = models.FloatField(default=0)

    # Outputs (ML predicted)
    target_area_cm2 = models.FloatField(default=0)
    target_Ix_cm4 = models.FloatField(default=0)
    target_Iz_cm4 = models.FloatField(default=0)
    target_depth_mm = models.FloatField(default=0)
    target_width_mm = models.FloatField(default=0)
    target_weight_kgm = models.FloatField(default=0)
    scale_factor = models.FloatField(default=1.0)

    def __str__(self):
        return f"{self.member_type} #{self.member_id}"

    @property
    def utilization_status(self):
        if self.utilization > 1.0:
            return 'over'
        elif self.utilization < 0.5:
            return 'under'
        return 'safe'