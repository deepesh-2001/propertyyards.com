"""
Report Scheduler
Schedule daily Excel report generation and email sending
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)


class ReportScheduler:
    """Scheduler for daily reports"""
    
    def __init__(self, database, email_service):
        self.db = database
        self.email_service = email_service
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        """Start the scheduler"""
        # Schedule daily report at 9:00 AM every day
        self.scheduler.add_job(
            self.send_daily_report,
            CronTrigger(hour=9, minute=0),
            id='daily_report',
            name='Daily Report',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Report scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Report scheduler stopped")
    
    async def send_daily_report(self):
        """Generate and send daily report via email"""
        try:
            from app.reports import ReportGenerator
            
            report_generator = ReportGenerator(self.db)
            
            # Generate daily summary report
            report_data = await report_generator.generate_daily_summary_report()
            
            # Get admin users to send report to
            admin_users = await self.db.users.find({"role": "admin"}).to_list(length=10)
            
            if not admin_users:
                logger.warning("No admin users found to send report to")
                return
            
            # Send report to each admin
            for admin in admin_users:
                admin_email = admin.get("email")
                if admin_email:
                    # Save report to file (in production, use cloud storage)
                    report_filename = f"daily_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
                    
                    # Send email with report
                    subject = f"Daily Report - {datetime.now().strftime('%Y-%m-%d')}"
                    body = f"""
                    <html>
                    <body>
                        <h2>Daily Report - {datetime.now().strftime('%Y-%m-%d')}</h2>
                        <p>Please find attached the daily summary report.</p>
                        <p>Report includes:</p>
                        <ul>
                            <li>New users</li>
                            <li>New properties</li>
                            <li>New inquiries</li>
                            <li>New leads</li>
                        </ul>
                        <p>Best regards,<br>PropertyYards Team</p>
                    </body>
                    </html>
                    """
                    
                    # Note: In production, you would attach the Excel file
                    # For now, we'll send a notification
                    await self.email_service.send_email(
                        to_email=admin_email,
                        subject=subject,
                        body=body,
                        from_email="reports@propertyyards.com",
                        from_name="PropertyYards Reports",
                        html=True
                    )
                    
                    logger.info(f"Daily report sent to {admin_email}")
            
            logger.info("Daily report generation completed")
            
        except Exception as e:
            logger.error(f"Error sending daily report: {e}")
    
    async def send_custom_report(
        self,
        report_type: str,
        recipients: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ):
        """Generate and send custom report"""
        try:
            from app.reports import ReportGenerator
            
            report_generator = ReportGenerator(self.db)
            
            # Generate report based on type
            if report_type == "property_listings":
                report_data = await report_generator.generate_property_listings_report(start_date, end_date)
            elif report_type == "user_activity":
                report_data = await report_generator.generate_user_activity_report(start_date, end_date)
            elif report_type == "inquiries":
                report_data = await report_generator.generate_inquiries_report(start_date, end_date)
            elif report_type == "leads":
                report_data = await report_generator.generate_leads_report(start_date, end_date)
            elif report_type == "broker_performance":
                report_data = await report_generator.generate_broker_performance_report(start_date, end_date)
            elif report_type == "rental_report":
                report_data = await report_generator.generate_rental_report(start_date, end_date)
            else:
                report_data = await report_generator.generate_daily_summary_report()
            
            # Send report to recipients
            for recipient in recipients:
                subject = f"{report_type.replace('_', ' ').title()} Report"
                body = f"""
                <html>
                <body>
                    <h2>{subject}</h2>
                    <p>Please find attached the requested report.</p>
                    <p>Report period: {start_date} to {end_date}</p>
                    <p>Best regards,<br>PropertyYards Team</p>
                </body>
                </html>
                """
                
                await self.email_service.send_email(
                    to_email=recipient,
                    subject=subject,
                    body=body,
                    from_email="reports@propertyyards.com",
                    from_name="PropertyYards Reports",
                    html=True
                )
                
                logger.info(f"{report_type} report sent to {recipient}")
            
            logger.info(f"Custom {report_type} report generation completed")
            
        except Exception as e:
            logger.error(f"Error sending custom report: {e}")
            raise
