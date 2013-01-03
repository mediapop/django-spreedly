# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Subscription.store_credit'
        db.add_column('spreedly_subscription', 'store_credit',
                      self.gf('django.db.models.fields.DecimalField')(default='0', max_digits=6, decimal_places=2),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Subscription.store_credit'
        db.delete_column('spreedly_subscription', 'store_credit')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'spreedly.fee': {
            'Meta': {'object_name': 'Fee'},
            'default_amount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '6', 'decimal_places': '2'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['spreedly.FeeGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'plan': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['spreedly.Plan']"})
        },
        'spreedly.feegroup': {
            'Meta': {'object_name': 'FeeGroup'},
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'primary_key': 'True'})
        },
        'spreedly.gift': {
            'Meta': {'object_name': 'Gift'},
            'created_at': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'from_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'gifts_sent'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'message': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'plan_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'sent_at': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'to_user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'gifts_received'", 'to': "orm['auth.User']"}),
            'uuid': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32', 'db_index': 'True'})
        },
        'spreedly.lineitem': {
            'Meta': {'object_name': 'LineItem'},
            'amount': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '6', 'decimal_places': '2'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'error_code': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'fee': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['spreedly.Fee']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'issued_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'reference': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'started': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'successfull': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'spreedly.plan': {
            'Meta': {'ordering': "['name']", 'object_name': 'Plan'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'date_changed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'duration_quantity': ('django.db.models.fields.IntegerField', [], {'default': '0', 'blank': 'True'}),
            'duration_units': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'feature_level': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'force_recurring': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.IntegerField', [], {'primary_key': 'True', 'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'needs_to_be_renewed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'plan_type': ('django.db.models.fields.CharField', [], {'max_length': '10', 'blank': 'True'}),
            'price': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'null': 'True', 'max_digits': '6', 'decimal_places': '2'}),
            'return_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'spreedly_site_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'terms': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'version': ('django.db.models.fields.IntegerField', [], {'default': '1', 'blank': 'True'})
        },
        'spreedly.subscription': {
            'Meta': {'object_name': 'Subscription'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'active_until': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'card_expires_before_next_auto_renew': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'eligible_for_free_trial': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'feature_level': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'lifetime': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'plan': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['spreedly.Plan']", 'null': 'True'}),
            'recurring': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'store_credit': ('django.db.models.fields.DecimalField', [], {'default': "'0'", 'max_digits': '6', 'decimal_places': '2'}),
            'token': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['spreedly']