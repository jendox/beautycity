from django.urls import path

from appointments import api_views

urlpatterns = [
    path("availability/dates/", api_views.AvailabilityDatesAPIView.as_view(), name="api_availability_dates"),
    path("availability/slots/", api_views.AvailabilitySlotsAPIView.as_view(), name="api_availability_slots"),
    path(
        "masters/<int:master_id>/availability/",
        api_views.MasterAvailabilityAPIView.as_view(),
        name="api_master_availability",
    ),
    path("booking/holds/", api_views.BookingHoldListCreateAPIView.as_view(), name="api_booking_holds"),
    path("booking/holds/<str:hold_id>/", api_views.BookingHoldDetailAPIView.as_view(), name="api_booking_hold_detail"),
    path(
        "booking/holds/<str:hold_id>/apply-promo/",
        api_views.BookingHoldApplyPromoAPIView.as_view(),
        name="api_booking_hold_apply_promo",
    ),
    path("appointments/", api_views.AppointmentCreateAPIView.as_view(), name="api_appointments_create"),
    path("me/appointments/", api_views.MyAppointmentsAPIView.as_view(), name="api_me_appointments"),
]
