function toggleNotifications(event) {
    if (event) {
        event.stopPropagation();
    }
    
    const panel = document.getElementById('notificationsPanel');
    if (!panel) return;
    
    if (panel.style.display === 'block') {
        panel.style.display = 'none';
    } else {
        panel.style.display = 'block';
        loadNotifications();
    }
}

function loadNotifications() {
    fetch('/get_notifications')
    .then(response => response.json())
    .then(data => {
        const container = document.querySelector('.notifications-list');
        if (!container) return;
        
        if (data.notifications && data.notifications.length > 0) {
            container.innerHTML = data.notifications.map(notification => `
                <div class="notification-item ${notification.is_read ? '' : 'unread'}" 
                     onclick="markAsRead(${notification.id}, this)">
                    <div class="notification-message">${notification.message}</div>
                    <div class="notification-date">${formatDate(notification.created_at)}</div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<div class="notification-item">Нет уведомлений</div>';
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
    });
}

function markAsRead(notificationId, element) {
    if (element) element.classList.remove('unread');
    
    fetch('/mark_notification_read', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({notification_id: notificationId})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const badge = document.querySelector('.notification-badge');
            if (badge) {
                const count = parseInt(badge.textContent) - 1;
                if (count > 0) {
                    badge.textContent = count;
                } else {
                    badge.remove();
                }
            }
        }
    });
}

function markAllAsRead() {
    fetch('/mark_all_notifications_read', {method: 'POST'})
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.querySelectorAll('.notification-item.unread').forEach(item => {
                item.classList.remove('unread');
            });
            const badge = document.querySelector('.notification-badge');
            if (badge) badge.remove();
        }
    });
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('ru-RU', {
        day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit'
    });
}

function showSection(sectionName, buttonElement) {
    document.querySelectorAll('.section-content').forEach(section => {
        section.style.display = 'none';
    });
    
    document.querySelectorAll('.category-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const targetSection = document.getElementById(sectionName + '-section');
    if (targetSection) {
        targetSection.style.display = 'block';
        if (sectionName === 'requests') {
            loadTeacherRequests();
        }
    }
    
    if (buttonElement) {
        buttonElement.classList.add('active');
    }
}

function openRentalAgreement(equipmentId) {
    fetch('/get_equipment_info/' + equipmentId)
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            alert('Ошибка получения данных');
            return;
        }
        
        const eq = data.equipment;
        const user = data.user;
        const today = new Date().toLocaleDateString('ru-RU');
        
        const agreementHTML = `
            <div style="font-family: Arial, sans-serif; max-width: 700px; padding: 20px;">
                <h2 style="text-align: center;">ДОГОВОР АРЕНДЫ ОБОРУДОВАНИЯ</h2>
                <p><strong>Дата:</strong> ${today}</p>
                <p><strong>Арендатор:</strong> ${user.full_name}</p>
                <p><strong>Учебное заведение:</strong> ${user.school}</p>
                <p><strong>Класс:</strong> ${user.class}</p>
                <hr>
                <h3>Предмет аренды:</h3>
                <p><strong>Наименование:</strong> ${eq.name}</p>
                <p><strong>Описание:</strong> ${eq.description || 'Не указано'}</p>
                <p><strong>Категория:</strong> ${eq.category}</p>
                <hr>
                <h3>Условия аренды:</h3>
                <ol>
                    <li>Арендатор обязуется вернуть оборудование в исправном состоянии</li>
                    <li>В случае поломки арендатор несет материальную ответственность</li>
                    <li>Срок аренды устанавливается администратором школы</li>
                    <li>Запрещается передача оборудования третьим лицам</li>
                </ol>
                <p style="margin-top: 30px;">Подпись арендатора: _________________________</p>
                <p>Подпись администратора: _________________________</p>
            </div>
        `;
        
        document.getElementById('agreementContent').innerHTML = agreementHTML;
        document.getElementById('agreementModal').style.display = 'flex';
        document.getElementById('agreementModal').setAttribute('data-equipment-id', equipmentId);
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Ошибка загрузки данных');
    });
}

function closeAgreementModal() {
    document.getElementById('agreementModal').style.display = 'none';
}

function printAgreement() {
    const content = document.getElementById('agreementContent').innerHTML;
    const printWindow = window.open('', '', 'width=800,height=600');
    printWindow.document.write('<html><head><title>Договор аренды</title></head><body>');
    printWindow.document.write(content);
    printWindow.document.write('</body></html>');
    printWindow.document.close();
    printWindow.print();
}

function confirmAndSubmitRequest() {
    const equipmentId = document.getElementById('agreementModal').getAttribute('data-equipment-id');
    
    const formData = new FormData();
    formData.append('equipment_id', equipmentId);
    
    fetch('/request_equipment', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Заявка успешно подана!');
            closeAgreementModal();
            location.reload();
        } else {
            alert('Ошибка: ' + (data.error || 'Неизвестная ошибка'));
        }
    })
    .catch(error => {
        console.error('Ошибка:', error);
        alert('Ошибка при отправке заявки');
    });
}

function loadTeacherRequests() {
    const container = document.getElementById('teacher-requests-list');
    if (!container) return;
    
    container.innerHTML = '<p>Загрузка...</p>';
    
    fetch('/teacher_requests')
    .then(response => response.json())
    .then(data => {
        if (data.success && data.requests && data.requests.length > 0) {
            container.innerHTML = data.requests.map(request => {
                let actionsHTML = '';
                if (request.status === 'pending') {
                    actionsHTML = `
                        <div class="teacher-actions">
                            <button class="action-btn btn-approve" onclick="approveRequest(${request.id})">ОДОБРИТЬ</button>
                            <button class="action-btn btn-reject" onclick="rejectRequest(${request.id})">ОТКЛОНИТЬ</button>
                        </div>`;
                } else if (request.status === 'approved') {
                    actionsHTML = `
                        <div class="teacher-actions">
                            <button class="action-btn btn-return" onclick="returnRequest(${request.id})">ВОЗВРАТ</button>
                        </div>`;
                }
                
                return `
                    <div class="request-item">
                        <div class="request-header">
                            <h3>${request.equipment_name || 'Оборудование'}</h3>
                            <span class="request-status status-${request.status}">${getStatusText(request.status)}</span>
                        </div>
                        <p><strong>Ученик:</strong> ${request.student_name || 'Неизвестный'}</p>
                        <p><strong>Дата:</strong> ${request.request_date || ''}</p>
                        ${request.due_date ? `<p><strong>Вернуть до:</strong> ${request.due_date}</p>` : ''}
                        ${actionsHTML}
                    </div>`;
            }).join('');
        } else {
            container.innerHTML = '<p>Нет заявок</p>';
        }
    })
    .catch(error => {
        container.innerHTML = '<p>Ошибка загрузки</p>';
    });
}

function approveRequest(requestId) {
    const date = prompt('Введите дату возврата (ГГГГ-ММ-ДД):', '2025-12-31');
    if (date) updateRequestStatus(requestId, 'approved', date);
}

function rejectRequest(requestId) {
    if (confirm('Отклонить заявку?')) updateRequestStatus(requestId, 'rejected');
}

function returnRequest(requestId) {
    if (confirm('Отметить возврат?')) updateRequestStatus(requestId, 'returned');
}

function updateRequestStatus(requestId, status, dueDate = null) {
    const formData = new FormData();
    formData.append('request_id', requestId);
    formData.append('status', status);
    if (dueDate) formData.append('due_date', dueDate);
    
    fetch('/update_request_status', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Статус обновлен!');
            loadTeacherRequests();
        } else {
            alert('Ошибка: ' + data.error);
        }
    })
    .catch(error => {
        alert('Ошибка сети');
    });
}

function getStatusText(status) {
    const map = {pending: 'ОЖИДАЕТ', approved: 'ОДОБРЕНО', rejected: 'ОТКЛОНЕНО', returned: 'ВОЗВРАЩЕНО'};
    return map[status] || status;
}

function showAddEquipmentForm() {
    document.getElementById('addEquipmentModal').style.display = 'flex';
}

function hideAddEquipmentForm() {
    document.getElementById('addEquipmentModal').style.display = 'none';
}

function openProfileModal() {
    document.getElementById('profileModal').style.display = 'block';
}

function closeProfileModal() {
    document.getElementById('profileModal').style.display = 'none';
}

document.addEventListener('DOMContentLoaded', function() {
    const notificationIcon = document.getElementById('notificationIcon');
    if (notificationIcon) {
        notificationIcon.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleNotifications(e);
        });
    }
    
    document.addEventListener('click', function(e) {
        const panel = document.getElementById('notificationsPanel');
        const icon = document.getElementById('notificationIcon');
        if (panel && !panel.contains(e.target) && !icon.contains(e.target)) {
            panel.style.display = 'none';
        }
    });
    
    const equipmentForm = document.getElementById('addEquipmentForm');
    if (equipmentForm) {
        equipmentForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const btn = this.querySelector('button[type="submit"]');
            btn.disabled = true;
            btn.textContent = 'ДОБАВЛЯЕМ...';
            
            fetch('/add_equipment', {
                method: 'POST',
                body: new FormData(this)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Оборудование добавлено!');
                    hideAddEquipmentForm();
                    location.reload();
                } else {
                    alert('Ошибка: ' + data.error);
                    btn.disabled = false;
                    btn.textContent = 'ДОБАВИТЬ';
                }
            })
            .catch(error => {
                alert('Ошибка сети');
                btn.disabled = false;
                btn.textContent = 'ДОБАВИТЬ';
            });
        });
    }
    
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', function(e) {
            e.preventDefault();
            fetch('/update_profile', {
                method: 'POST',
                body: new FormData(this)
            })
            .then(response => response.text())
            .then(data => {
                if (data === 'Профиль обновлен') {
                    alert('Профиль обновлен!');
                    closeProfileModal();
                    location.reload();
                } else {
                    alert('Ошибка: ' + data);
                }
            });
        });
    }
    
    window.onclick = function(event) {
        if (event.target === document.getElementById('addEquipmentModal')) hideAddEquipmentForm();
        if (event.target === document.getElementById('profileModal')) closeProfileModal();
        if (event.target === document.getElementById('agreementModal')) closeAgreementModal();
    };
});