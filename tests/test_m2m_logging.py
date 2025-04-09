import pytest
from tests.models import Article, Tag
from easyaudit.models import CRUDEvent


@pytest.mark.django_db
def test_m2m_logging_full():
    
    article = Article.objects.create(title="Test Article")
    tag1 = Tag.objects.create(name="django")
    tag2 = Tag.objects.create(name="pytest")

    
    CRUDEvent.objects.all().delete()

    # --- M2M_ADD ---
    article.tags.add(tag1)
    assert CRUDEvent.objects.filter(event_type=CRUDEvent.M2M_ADD).exists(), 

    # --- M2M_REMOVE ---
    article.tags.remove(tag1)
    assert CRUDEvent.objects.filter(event_type=CRUDEvent.M2M_REMOVE).exists(), 

    # --- M2M_CLEAR ---
    article.tags.add(tag1, tag2)
    article.tags.clear()
    assert CRUDEvent.objects.filter(event_type=CRUDEvent.M2M_CLEAR).exists(), 
