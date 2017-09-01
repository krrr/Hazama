#include "datetimedialog.h"
#include <QDateTimeEdit>
#include <QBoxLayout>
#include <QDialogButtonBox>


DateTimeDialog::DateTimeDialog(QDateTime dt, const QString &displayFmt, QWidget *parent) :
        QDialog(parent) {
    setWindowFlags(Qt::Window | Qt::WindowCloseButtonHint);
    setWindowModality(Qt::WindowModal);
    format = displayFmt;
    setWindowTitle(tr("Edit datetime"));
    auto verticalLayout = new QVBoxLayout(this);
    dtEdit = new QDateTimeEdit(dt, this);
    dtEdit->setDisplayFormat(displayFmt);
    verticalLayout->addWidget(dtEdit);
    auto btnBox = new QDialogButtonBox(this);
    btnBox->setOrientation(Qt::Horizontal);
    btnBox->setStandardButtons(QDialogButtonBox::Ok | QDialogButtonBox::Cancel);
    verticalLayout->addWidget(btnBox);
    connect(btnBox, &QDialogButtonBox::accepted, this, &QDialog::accept);
    connect(btnBox, &QDialogButtonBox::rejected, this, &QDialog::reject);
}

QDateTime DateTimeDialog::getDateTime(QDateTime dt, const QString &displayFmt, QWidget *parent) {
    DateTimeDialog dialog(dt, displayFmt, parent);
    int ret = dialog.exec();
    return (ret == QDialog::Accepted) ? dialog.dtEdit->dateTime() : QDateTime();
}
