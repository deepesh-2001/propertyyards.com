"""
Travel Services Test Suite
Tests for cab, train, hotel booking services and travel lead auto-generation
"""
import pytest
import sys
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

sys.path.insert(0, 'C:/Users/deepe/PyCharmMiscProject/housing_platform/backend')


# ============================================================
# CAB SERVICE TESTS
# ============================================================

class TestCabBookingService:

    @pytest.fixture
    def service(self):
        from app.cab_booking_service import CabBookingService
        svc = CabBookingService()
        return svc

    @pytest.mark.asyncio
    async def test_initialize_no_keys(self, service):
        await service.initialize()
        assert all(not c["enabled"] for c in service.providers.values())

    @pytest.mark.asyncio
    async def test_initialize_with_keys(self, service):
        await service.initialize(ola_api_key="test_key", uber_server_token="uber_tok")
        assert service.providers["ola"]["enabled"] is True
        assert service.providers["uber"]["enabled"] is True
        assert service.providers["rapido"]["enabled"] is False

    @pytest.mark.asyncio
    async def test_mock_estimates_returns_sorted_offers(self, service):
        offers = await service.get_estimates(28.6, 77.2, 28.65, 77.25)
        assert len(offers) > 0
        fares = [o.estimated_fare for o in offers]
        assert fares == sorted(fares)

    @pytest.mark.asyncio
    async def test_mock_estimates_covers_all_providers(self, service):
        offers = await service.get_estimates(28.6, 77.2, 28.65, 77.25)
        providers = {o.provider for o in offers}
        assert "Ola" in providers
        assert "Uber" in providers
        assert "Rapido" in providers

    @pytest.mark.asyncio
    async def test_mock_estimates_validates_distance(self, service):
        offers = await service.get_estimates(0.0, 0.0, 0.0, 0.0)
        assert all(o.estimated_distance_km >= 2 for o in offers)

    @pytest.mark.asyncio
    async def test_book_cab_creates_booking(self, service):
        booking = await service.book_cab(
            user_id="user1",
            offer_id="ola_mini_abc123",
            pickup_lat=28.6,
            pickup_lng=77.2,
            pickup_address="Connaught Place, Delhi",
            drop_lat=28.65,
            drop_lng=77.25,
            drop_address="Karol Bagh, Delhi",
            estimated_fare=250.0,
            provider="Ola",
            category="mini"
        )
        assert booking.booking_id is not None
        assert booking.user_id == "user1"
        assert booking.otp is not None
        assert len(booking.otp) == 4
        assert service.bookings[booking.booking_id] == booking

    @pytest.mark.asyncio
    async def test_cancel_booking_not_found(self, service):
        result = await service.cancel_booking("nonexistent")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_cancel_booking_success(self, service):
        booking = await service.book_cab(
            user_id="u1", offer_id="x", pickup_lat=0, pickup_lng=0,
            pickup_address="A", drop_lat=1, drop_lng=1,
            drop_address="B", estimated_fare=100, provider="Ola", category="mini"
        )
        result = await service.cancel_booking(booking.booking_id)
        assert result["success"] is True
        from app.cab_booking_service import CabStatus
        assert service.bookings[booking.booking_id].status == CabStatus.CANCELLED


# ============================================================
# TRAIN SERVICE TESTS
# ============================================================

class TestTrainBookingService:

    @pytest.fixture
    def service(self):
        from app.train_booking_service import TrainBookingService
        return TrainBookingService()

    @pytest.mark.asyncio
    async def test_initialize_no_keys(self, service):
        await service.initialize()
        assert all(not c["enabled"] for c in service.providers.values())

    @pytest.mark.asyncio
    async def test_search_returns_mock_trains(self, service):
        trains = await service.search_trains("NDLS", "BCT", "2026-06-01")
        assert len(trains) > 0
        assert all(t.origin_code == "NDLS" for t in trains)
        assert all(t.destination_code == "BCT" for t in trains)

    @pytest.mark.asyncio
    async def test_search_trains_have_classes(self, service):
        trains = await service.search_trains("NDLS", "BCT", "2026-06-01")
        for train in trains:
            assert len(train.available_classes) > 0
            class_codes = [c["class_code"] for c in train.available_classes]
            assert "SL" in class_codes

    @pytest.mark.asyncio
    async def test_fare_estimation(self, service):
        sl_fare = service._estimate_fare("SL", 1000)
        ac1_fare = service._estimate_fare("1A", 1000)
        assert ac1_fare > sl_fare

    @pytest.mark.asyncio
    async def test_check_availability_mock(self, service):
        result = await service.check_availability("12951", "NDLS", "BCT", "2026-06-01", "SL")
        assert "available" in result
        assert result["source"] == "mock"

    @pytest.mark.asyncio
    async def test_book_train_creates_record(self, service):
        booking = await service.book_train(
            user_id="user1",
            train_number="12951",
            train_name="MUMBAI RAJDHANI",
            travel_date="2026-06-01",
            from_station="NDLS",
            to_station="BCT",
            travel_class="SL",
            passengers=[{"name": "John Doe", "age": 30, "gender": "M"}],
            total_fare=850.0
        )
        assert booking.booking_id is not None
        assert len(booking.pnr) == 10
        assert booking.total_fare == 850.0
        assert booking.base_fare == pytest.approx(850.0 * 0.95, rel=0.01)
        assert service.bookings[booking.booking_id] == booking

    @pytest.mark.asyncio
    async def test_cancel_booking(self, service):
        booking = await service.book_train(
            user_id="u1", train_number="12951", train_name="RAJ",
            travel_date="2026-06-01", from_station="NDLS", to_station="BCT",
            travel_class="SL", passengers=[{"name": "A", "age": 25, "gender": "M"}],
            total_fare=500.0
        )
        result = await service.cancel_booking(booking.booking_id)
        assert result["success"] is True
        assert result["refund_amount"] == pytest.approx(500 * 0.75, rel=0.01)

        from app.train_booking_service import BookingStatus
        assert service.bookings[booking.booking_id].status == BookingStatus.CANCELLED


# ============================================================
# HOTEL SERVICE TESTS
# ============================================================

class TestHotelBookingService:

    @pytest.fixture
    def service(self):
        from app.hotel_booking_service import HotelBookingService
        return HotelBookingService()

    @pytest.mark.asyncio
    async def test_initialize_no_keys(self, service):
        await service.initialize()
        assert all(not c["enabled"] for c in service.providers.values())

    @pytest.mark.asyncio
    async def test_search_returns_mock_hotels(self, service):
        hotels = await service.search_hotels(
            city="Delhi", check_in="2026-06-10",
            check_out="2026-06-12", adults=2
        )
        assert len(hotels) > 0
        for h in hotels:
            assert h.nights == 2
            assert len(h.rooms) > 0

    @pytest.mark.asyncio
    async def test_search_sorted_by_price(self, service):
        hotels = await service.search_hotels("Mumbai", "2026-07-01", "2026-07-03", 2)
        prices = [h.rooms[0].price_per_night for h in hotels]
        assert prices == sorted(prices)

    @pytest.mark.asyncio
    async def test_search_filter_min_stars(self, service):
        hotels = await service.search_hotels("Delhi", "2026-06-10", "2026-06-12", min_stars=4)
        for h in hotels:
            assert h.star_rating >= 4

    @pytest.mark.asyncio
    async def test_calc_nights(self, service):
        assert service._calc_nights("2026-06-01", "2026-06-03") == 2
        assert service._calc_nights("2026-06-01", "2026-06-01") == 1

    @pytest.mark.asyncio
    async def test_book_hotel_creates_record(self, service):
        booking = await service.book_hotel(
            user_id="user1",
            hotel_id="mock_0",
            hotel_name="Taj Hotel",
            hotel_address="New Delhi, India",
            room_type="deluxe",
            room_name="Deluxe Room",
            check_in="2026-06-10",
            check_out="2026-06-12",
            guests=2,
            price_per_night=4500.0,
            total_price=9000.0,
            provider="Mock",
            guest_name="Jane Smith",
            guest_email="jane@example.com",
            guest_phone="+91-9876543210"
        )
        assert booking.booking_id is not None
        assert booking.confirmation_number.startswith("HB")
        assert booking.nights == 2
        assert booking.taxes == pytest.approx(9000 * 0.12, rel=0.01)
        assert booking.final_price == pytest.approx(9000 * 1.12, rel=0.01)

    @pytest.mark.asyncio
    async def test_cancel_hotel_booking(self, service):
        booking = await service.book_hotel(
            user_id="u1", hotel_id="h1", hotel_name="Test Hotel",
            hotel_address="City, India", room_type="standard",
            room_name="Standard", check_in="2026-06-10", check_out="2026-06-12",
            guests=2, price_per_night=2000, total_price=4000,
            provider="Mock", guest_name="X", guest_email="x@x.com", guest_phone="123"
        )
        result = await service.cancel_booking(booking.booking_id)
        assert result["success"] is True
        assert result["refund_amount"] == pytest.approx(4000 * 0.80, rel=0.01)


# ============================================================
# TRAVEL LEAD SERVICE TESTS
# ============================================================

class TestTravelLeadService:

    @pytest.fixture
    def service(self):
        from app.travel_lead_service import TravelLeadService
        return TravelLeadService()

    @pytest.mark.asyncio
    @patch("app.travel_lead_service.TravelLeadService._persist_lead", new_callable=AsyncMock)
    async def test_cab_estimate_no_lead_on_generic_route(self, mock_persist, service):
        lead = await service.create_lead_from_cab_estimate(
            user_id="u1", user_email="a@b.com", user_phone=None,
            pickup_lat=28.6, pickup_lng=77.2, drop_lat=28.65, drop_lng=77.25
        )
        assert lead is None
        mock_persist.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.travel_lead_service.TravelLeadService._persist_lead", new_callable=AsyncMock)
    async def test_cab_estimate_creates_lead_for_property_area(self, mock_persist, service):
        lead = await service.create_lead_from_cab_estimate(
            user_id="u1", user_email="a@b.com", user_phone=None,
            pickup_lat=28.6, pickup_lng=77.2, drop_lat=28.65, drop_lng=77.25,
            pickup_address="DLF Phase 2, Gurgaon",
            drop_address="Sector 14, Noida"
        )
        assert lead is not None
        assert "property_area_visit" in lead.intent_tags
        from app.travel_lead_service import LeadPriority
        assert lead.priority == LeadPriority.HOT

    @pytest.mark.asyncio
    @patch("app.travel_lead_service.TravelLeadService._persist_lead", new_callable=AsyncMock)
    async def test_cab_booking_always_creates_lead(self, mock_persist, service):
        lead = await service.create_lead_from_cab_booking(
            user_id="u1", user_email="a@b.com", user_phone="9876543210",
            booking_id="bk1", pickup_address="Mall Road",
            pickup_lat=28.6, pickup_lng=77.2,
            drop_address="Railway Station",
            drop_lat=28.7, drop_lng=77.3,
            estimated_fare=300, provider="Ola", category="sedan"
        )
        assert lead is not None
        assert "cab_booked" in lead.intent_tags
        mock_persist.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.travel_lead_service.TravelLeadService._persist_lead", new_callable=AsyncMock)
    async def test_train_booking_creates_high_priority_lead(self, mock_persist, service):
        lead = await service.create_lead_from_train_booking(
            user_id="u1", user_email="a@b.com", user_phone="9876543210",
            booking_id="bk2", from_station="NDLS", to_station="BCT",
            travel_date="2026-06-01", train_name="RAJDHANI", total_fare=1200
        )
        assert lead is not None
        from app.travel_lead_service import LeadPriority
        assert lead.priority == LeadPriority.HIGH
        assert f"destination:BCT" in lead.intent_tags

    @pytest.mark.asyncio
    @patch("app.travel_lead_service.TravelLeadService._persist_lead", new_callable=AsyncMock)
    async def test_hotel_long_stay_creates_hot_lead(self, mock_persist, service):
        lead = await service.create_lead_from_hotel_booking(
            user_id="u1", user_email="a@b.com", user_phone="9876543210",
            booking_id="bk3", hotel_name="Taj Hotel",
            hotel_address="Mumbai, India", city="Mumbai",
            check_in="2026-06-01", check_out="2026-06-15",
            nights=14, guests=2, final_price=85000,
            guest_name="John Doe", guest_phone="9876543210"
        )
        assert lead is not None
        from app.travel_lead_service import LeadPriority
        assert lead.priority == LeadPriority.HOT
        assert "long_stay" in lead.intent_tags
        assert "relocation_strong_signal" in lead.intent_tags

    @pytest.mark.asyncio
    @patch("app.travel_lead_service.TravelLeadService._persist_lead", new_callable=AsyncMock)
    async def test_hotel_short_stay_high_priority(self, mock_persist, service):
        lead = await service.create_lead_from_hotel_booking(
            user_id="u1", user_email="a@b.com", user_phone=None,
            booking_id="bk4", hotel_name="OYO", hotel_address="Delhi, India",
            city="Delhi", check_in="2026-06-01", check_out="2026-06-03",
            nights=2, guests=1, final_price=3000,
            guest_name="A", guest_phone="111"
        )
        from app.travel_lead_service import LeadPriority
        assert lead.priority == LeadPriority.HIGH

    def test_get_leads_by_city(self, service):
        from app.travel_lead_service import TravelLead, LeadSource, LeadPriority, LeadStatus
        lead = TravelLead(
            lead_id="l1", user_id="u1", user_email=None, user_phone=None,
            source=LeadSource.HOTEL_BOOKING, priority=LeadPriority.HIGH,
            status=LeadStatus.NEW, city="MUMBAI"
        )
        service.leads["l1"] = lead
        results = service.get_leads_by_city("mumbai")
        assert len(results) == 1
        assert results[0].lead_id == "l1"

    def test_get_hot_leads(self, service):
        from app.travel_lead_service import TravelLead, LeadSource, LeadPriority, LeadStatus
        for i, priority in enumerate([LeadPriority.HOT, LeadPriority.HIGH, LeadPriority.LOW]):
            service.leads[f"l{i}"] = TravelLead(
                lead_id=f"l{i}", user_id="u1", user_email=None, user_phone=None,
                source=LeadSource.CAB_BOOKING, priority=priority, status=LeadStatus.NEW
            )
        hot = service.get_hot_leads()
        assert len(hot) == 1
        assert hot[0].lead_id == "l0"


# ============================================================
# INPUT VALIDATION TESTS
# ============================================================

class TestInputValidation:

    def test_cab_estimate_invalid_lat(self):
        from app.routers.cabs import EstimateRequest
        with pytest.raises(Exception):
            EstimateRequest(pickup_lat=200, pickup_lng=77, drop_lat=28, drop_lng=77)

    def test_cab_estimate_invalid_lng(self):
        from app.routers.cabs import EstimateRequest
        with pytest.raises(Exception):
            EstimateRequest(pickup_lat=28, pickup_lng=200, drop_lat=28, drop_lng=77)

    def test_cab_book_invalid_fare(self):
        from app.routers.cabs import BookCabRequest
        with pytest.raises(Exception):
            BookCabRequest(
                offer_id="x", provider="Ola", category="mini",
                pickup_lat=28, pickup_lng=77, pickup_address="A",
                drop_lat=29, drop_lng=78, drop_address="B",
                estimated_fare=-50
            )

    def test_cab_book_invalid_provider(self):
        from app.routers.cabs import BookCabRequest
        with pytest.raises(Exception):
            BookCabRequest(
                offer_id="x", provider="FakeCab", category="mini",
                pickup_lat=28, pickup_lng=77, pickup_address="A",
                drop_lat=29, drop_lng=78, drop_address="B",
                estimated_fare=200
            )

    def test_train_invalid_station_code(self):
        from app.routers.trains import TrainSearchRequest
        with pytest.raises(Exception):
            TrainSearchRequest(from_station="TOOLONG_CODE", to_station="BCT", travel_date="2026-06-01")

    def test_train_invalid_date_format(self):
        from app.routers.trains import TrainSearchRequest
        with pytest.raises(Exception):
            TrainSearchRequest(from_station="NDLS", to_station="BCT", travel_date="01-06-2026")

    def test_train_invalid_class(self):
        from app.routers.trains import TrainSearchRequest
        with pytest.raises(Exception):
            TrainSearchRequest(from_station="NDLS", to_station="BCT",
                               travel_date="2026-06-01", travel_class="FIRST")

    def test_hotel_invalid_date(self):
        from app.routers.hotels import HotelSearchRequest
        with pytest.raises(Exception):
            HotelSearchRequest(city="Delhi", check_in="June 10", check_out="2026-06-12")

    def test_hotel_invalid_stars(self):
        from app.routers.hotels import HotelSearchRequest
        with pytest.raises(Exception):
            HotelSearchRequest(city="Delhi", check_in="2026-06-10",
                               check_out="2026-06-12", min_stars=6)

    def test_hotel_invalid_room_type(self):
        from app.routers.hotels import HotelBookRequest
        with pytest.raises(Exception):
            HotelBookRequest(
                hotel_id="h1", hotel_name="Test", hotel_address="Delhi",
                room_type="PENTHOUSE", room_name="Penthouse",
                check_in="2026-06-10", check_out="2026-06-12",
                guests=2, price_per_night=5000, total_price=10000,
                provider="Mock", guest_name="A",
                guest_email="invalid-email", guest_phone="123"
            )

    def test_passenger_invalid_age(self):
        from app.routers.trains import PassengerModel
        with pytest.raises(Exception):
            PassengerModel(name="John", age=0, gender="M")

    def test_passenger_invalid_gender(self):
        from app.routers.trains import PassengerModel
        with pytest.raises(Exception):
            PassengerModel(name="John", age=25, gender="X")
